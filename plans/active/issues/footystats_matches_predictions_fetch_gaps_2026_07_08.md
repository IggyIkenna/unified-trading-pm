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
    /plans/archive/2026_07/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
    /plans/archive/2026_07/sports_reference_backfill_oom_2026_06_22.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-08
author: unknown
last_updated: 2026-07-27
parent_epic: sports_master
priority: P2
source:
  sports_p2_history_reference_and_odds_2015_to_present-015 (slot-14, re-surfacing slot-7's 2026-07-08 20:10 UTC
  diagnosis)
assigned_vm: NA
resolved_by:
locked_by:
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/archive/2026_08/issues/footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md,
    instruments-service/instruments_service/engine/orchestrator/footystats.py,
  ]
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
- [x] ✅ [CODE] P2. **Add cup/continental-competition fixture-calendar awareness to footystats PREDICTIONS** — mirror
      the existing `EmptyConfirmedReason.EXPECTED_NO_FIXTURE` resolution already used for MATCHES
      (footystats.py:584/598) so no-fixture dates for UECL/UEL/UCL/SWISS_CUP/COPA_ARGENTINA/+37 more resolve to a
      terminal typed state instead of staying un-typed `pending_fetch` forever; add regression test on a cup
      competition's known off-days (repo: instruments-service) — **instruments-service@78636dd (slot-13 sonnet/high)**.
      **Root cause confirmed**: MATCHES already tracked `_captured_leagues` per date and, after processing the fetch,
      looped `for _exp_lid in sorted(set(_ft_expected) - _captured_leagues)` to `record_empty(EXPECTED_NO_FIXTURE)` for
      every expected league with no fixture that day (footystats.py:580-586, 594-600 pre-fix line numbers) — but
      `_fetch_footystats_predictions` had NO equivalent loop: it only wrote `record_captured` rows for leagues actually
      present in the response, so a cup/continental league not playing on a given date got no manifest row at all
      (neither `captured` nor `empty_confirmed`), leaving it `pending_fetch` forever regardless of how many times the
      backfill VM re-ran. **Fix**: added the identical per-league completion pattern to `_fetch_footystats_predictions`
      — track `_captured_leagues` as leagues are written, then after the write block loop over
      `sorted(set(_ft_expected) - _captured_leagues)` emitting `record_empty(EXPECTED_NO_FIXTURE)` per league; also
      replaced the old single date-aggregate `record_empty` in the "no predictions at all" branch with the same
      per-league loop (mirrors MATCHES' all-empty branch), so a day with zero predictions closes every expected league
      individually rather than one blanket row. Verified compatible with the sibling out-of-subscription write-gate fix
      (`instruments-service@1af6c92`, todo #1 above) that landed mid-session: its `continue` guard fires before my
      `_captured_leagues.add(...)`, and an out-of-subscription league is also absent from `_ft_expected`, so it never
      gets spuriously backfilled by my completion loop. Added 2 regression tests in
      `tests/unit/test_orchestrator_sports.py::TestFetchFootystatsPredictions`
      (`test_cup_league_with_no_fixture_today_records_empty_expected_no_fixture` — mixed captured+uncaptured league day;
      `test_all_leagues_off_today_records_empty_per_league` — zero-prediction day, asserts per-league not aggregate
      rows). Full `quality-gates.sh` green (ALL QUALITY GATES PASSED), shipped via quickmerge --agent. **Note**: this
      closes the WRITE-PATH bug going forward; existing already-seeded `pending_fetch` rows for cup competitions still
      need the re-verify/re-dispatch pass (todo #4 below) to clear.
- [x] ✅ [DATA] P3. **Root-cause footystats ODDS 1,264-row residual** — no investigation session has looked at this
      cluster; determine whether it shares the MATCHES or PREDICTIONS root cause or is a distinct third gap (repo:
      instruments-service). — docs-only (see Progress Log 2026-07-08 slot-9 entry + the 2 new todos below it).
- [ ] [DATA] P2. **BLOCKED-PREREQUISITES (2026-07-08, slot-8).** **Re-verify + re-dispatch footystats backfill VM after
      the above land** — once the two CODE fixes are shipped, re-run the typing pass, confirm `(footystats, MATCHES)` +
      `(footystats, PREDICTIONS)` + `(footystats, ODDS)` `pending_fetch == 0`, then flip
      `sports_p2_history_reference_and_odds_2015_to_present` item #5 (and contribute to unblocking item #7) (repo:
      instruments-service). **BLOCKED**: auto-dispatched to slot-8 immediately after todo #1 (MATCHES fix) closed —
      `dispatch_reason: "highest-rank queued task with prereqs met and no collision"` (priority-only dispatch, same
      known failure mode as the tradfi plan's task-10 precedent: the dispatcher's machine-readable `prereqs` don't
      encode this todo's own in-text dependency on todo #2 AND todo #3). This todo's literal gate ("once the two CODE
      fixes are shipped... confirm MATCHES + PREDICTIONS + ODDS pending_fetch == 0") requires ALL THREE of: todo #1 (✅
      done, instruments-service@1af6c92), todo #2 (PREDICTIONS cup fixture-calendar — ✅ **now done too**,
      instruments-service@78636dd, slot-13), and todo #3 (ODDS root-cause — ✅ done, see below, but its own #6 CODE fix
      is still `- [ ]`). Running the typing pass / backfill VM now would only re-confirm the SAME ODDS residual already
      diagnosed, wasting VM spend before todo #6 lands (same "VM re-run without the code fix reproduces the same
      residual" lesson this issue doc already documents for MATCHES). **Un-block sequence (UPDATED 2026-07-08 slot-9)**:
      todos #1 and #2 are both now shipped — only todo #6 (ODDS write-gate fix, see below) remains before this todo can
      genuinely re-dispatch and have its typing-pass re-verify closes `pending_fetch == 0` across all three data_types.
      **NOTE**: do NOT assume ODDS clears purely from todo #6 — the ~177-row ongoing gap for ALLSVENSKAN, J1_LEAGUE,
      MLS, ELITESERIEN, BRASILEIRAO (see todo #6) is NOT a subscription-scope issue and needs its own root-cause before
      it clears; and the 20 `attempted_failed`/`phantom_captured_no_parquet_at_canonical_path` rows are OUT of the
      `pending_fetch` figure entirely and need todo #7 instead.
- [x] ✅ [CODE] P2. **Extend the confirmed subscription-scope write-gate fix (todo #1, instruments-service@1af6c92) to
      ODDS, plus root-cause a separate 5-league gap ODDS alone shows** — instruments-service@e951813 (slot-6
      sonnet/high). **Part 1 (write-gate)**: added the identical `if _canonical not in set(_ft_expected): drop` guard
      (mirroring footystats.py:198-203/543-548) to `_fetch_footystats_odds`'s per-league write loop, so the 5
      `PRED_NO_FOOTYSTATS`-excluded leagues no longer leak into ODDS coverage as `captured`. **Part 2 (5-league gap root
      cause)**: read the live `_index/availability_index.parquet` ONCE (single-walk discipline; cached locally for
      repeated analysis) and joined ODDS `expected_unattempted` rows against MATCHES rows for the same (date, league):
      **990 of the 1,264 total ODDS `pending_fetch` rows (78%) correlate 1:1 with a MATCHES `empty_confirmed` row for
      the identical (date, league)** — i.e. no fixture that day for that league, while OTHER leagues DID have fixtures
      that day (so `odds_rows` was non-empty overall and the date-level skip never fired). Confirmed
      `_fetch_footystats_odds` was missing the exact per-league fixture-calendar completion loop PREDICTIONS got in todo
      #2 below: its per-league write loop only ever iterated over leagues actually PRESENT in the API response, so a
      league with zero fixtures that date got no manifest row at all — neither `captured` nor `empty_confirmed` —
      leaving it `pending_fetch` forever regardless of backfill VM re-runs. The apparent "5-league" concentration in the
      original diagnosis (ALLSVENSKAN, J1_LEAGUE, MLS, ELITESERIEN, BRASILEIRAO) is explained by June being off-season
      for most European top leagues (so `/todays-matches` often returns rows for OTHER competitions, keeping the
      date-level skip from firing) while these 5 calendar-year leagues are genuinely in-season and therefore hit this
      gap far more visibly during that window — not a league-specific bug. **Fix**: added the identical
      `_captured_leagues` completion pattern to `_fetch_footystats_odds` (tracks captured leagues during the per-league
      write loop, then loops `sorted(set(_ft_expected) - _captured_leagues)` emitting
      `record_empty(EXPECTED_NO_FIXTURE)`), plus replaced the old single date-aggregate `record_empty` in the "no odds
      data at all" branch with the same per-league loop (mirrors PREDICTIONS' all-empty-day fix). Added 4 regression
      tests in `tests/unit/test_orchestrator_sports.py::TestFetchFootystatsOdds`
      (`test_out_of_subscription_league_dropped_not_captured`,
      `test_league_with_no_fixture_today_records_empty_expected_no_fixture`,
      `test_all_leagues_off_today_records_empty_per_league`, plus the existing `_ft_odds_stack` helper extended with an
      `expected_league_ids` param). Full `quality-gates.sh` green (ALL QUALITY GATES PASSED), shipped via quickmerge
      --agent. **Scope note**: like todo #1, this closes the WRITE-PATH bugs (prevents future recurrence going forward)
      but does NOT retroactively clean the existing ~1,264 pending_fetch ODDS rows already seeded in the live manifest —
      that data cleanup is todo #4's scope (re-run the typing pass after all CODE fixes land).
- [x] ✅ [DATA] P3. **Reconcile the 20 footystats ODDS
      `attempted_failed`/`phantom_captured_no_parquet_at_canonical_path` rows** — a DISTINCT, already-known issue class
      (manifest says an attempt was made but the parquet write is missing at the canonical path), NOT part of the
      `pending_fetch=1,264` figure (these are `attempted_failed`, not `expected_unattempted`) and NOT related to the
      write-gate root cause above. Existing tooling already handles this pattern
      (`scripts/reconcile_phantom_manifest_rows_all.py`, `scripts/dedup_phantom_after_recovery.py`) — run the existing
      reconciler scoped to `(source=footystats, data_type=ODDS)` rather than writing new code (repo:
      instruments-service). **— data-only fix, no code change (slot-12 sonnet/high).** `ODDS` is exclusively a
      footystats data_type (`SPORTS_DATA_TYPE_TO_FOLDER["ODDS"] = "footystats_odds"`,
      `unified-api-contracts/.../sports/gcs_paths.py`), so `--data-types ODDS` already scopes to `source=footystats` —
      no extra filter needed. Confirmed the manifest held 78 ODDS `attempted_failed` rows total (47
      `PipelineModeSourceMismatchError` + 19 `phantom_captured_no_parquet_at_canonical_path` + 11 `ArrowTypeError` + 1
      `RuntimeError`) — the 19+1=20 matches this todo's scope exactly; the 47+11=58 are a separate, out-of-scope issue
      class (different error_reasons, not mentioned in this todo) and were left untouched. Ran
      `scripts/reconcile_phantom_manifest_rows_all.py --asset-group sports --data-types ODDS --unphantom-only --dry-run`
      first: all 19 phantom-flagged rows now have real parquet at their canonical path (0 still-phantom) — the data
      exists on disk today (whether it always did or arrived since the earlier phantom-flip is unconfirmed, but the
      re-validation is unambiguous). Applied without `--dry-run`: manifest `captured` count 30,898→30,917 (+19),
      `attempted_failed` 78→59, `phantom_captured_no_parquet_at_canonical_path` count now 0. Safe-by-construction (this
      mode can only flip phantom→captured, never the reverse). Probed the single `RuntimeError` row separately
      (date=2026-01-13, blank league_id — `--unphantom` only re-validates
      `error_reason == 'phantom_captured_no_parquet_at_canonical_path'`, so it wasn't touched by the above): listed
      `sports_reference/by_date/day=2026-01-13/entity=footystats_odds/` directly — 0 blobs, confirming this row is a
      genuine capture failure (no parquet anywhere for that day), correctly tagged `attempted_failed`, NOT a phantom —
      nothing to reconcile; it's eligible for the normal backfill retry cadence like any other real failure. No
      instruments-service commit needed (data-only manifest fix, no code touched).

## Progress Log

- **2026-08-16 (slot-5, cross-reference only, not this doc's own task)**: the sibling blocker
  `footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md` is now fully resolved
  (`status: open` → `status: resolved`) — its own `[DIAG] P3` re-verify confirmed `pending_fetch` genuinely holds 0
  for the 4-league + 11-cup-league population across MATCHES/PREDICTIONS/ODDS, with the `entity_coverage` gate
  actively firing in production through 2026-08-15. This doc's own todo #4 ("re-verify + re-dispatch footystats
  backfill VM") had its re-verify half satisfied by that sibling's own re-verify (same manifest, same figures); the
  remaining half (re-dispatch a backfill VM, then flip the archived `sports_p2_history_reference_and_odds_2015_to_present`
  item #5) was NOT executed here — out of this session's assigned scope (a different task/doc), and likely
  unnecessary in practice since `pending_fetch=0` means there is nothing left to backfill. Left todo #4 as-is for a
  future pass to adjudicate the VM-dispatch/archived-plan-flip decision explicitly rather than silently closing it.

- **2026-07-27** — Re-checked todo #4's gate per `sports_satellite_ao_dispatch_batch4_2026_07_25.md` todo #1
  (data_engineering slot). A fresh single-walk read of `_index/availability_index.parquet`
  (`unified_trading_library.read_availability_index`) shows the 2026-07-12 zero-verification NO LONGER HOLDS:
  `(footystats, MATCHES)` pending_fetch=35,151, `(footystats, PREDICTIONS)` pending_fetch=35,151, `(footystats, ODDS)`
  pending_fetch=35,349. Per this todo's own instruction, NOT silently re-closing — this is a genuine regression,
  root-caused and filed as its own actionable finding:
  `issues/footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md`. Summary of that doc's
  root cause: NOT a write-path regression (the 2026-07-08 code fixes below are still correct and unaffected) — the
  sports canonical universe grew to ~300+ additional footystats-non-covered leagues since the last typing pass, and the
  existing non-covered-league typing scripts (`type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py`,
  `type_footystats_odds_non_covered_leagues_2026_06_29.py`) simply haven't been re-run against the larger universe. Live
  dry-run of both scripts confirms they account for 105,370 of the 105,651-row live total (99.7%). Todo #4 below and
  this doc's `status: open` are left UNCHANGED pending the new doc's remediation todos. **This doc's own checkbox #4
  stays `- [ ]` — not flipped.**
- **2026-07-08** — Todo #6 (extend write-gate fix to ODDS + root-cause 5-league gap) FLIPPED (slot-6 sonnet/high). See
  the todo's own entry above for the full write-up. Summary: (1) added the confirmed subscription-scope write-gate guard
  to `_fetch_footystats_odds`'s per-league write loop (mirrors todo #1); (2) root-caused the 5-league ongoing gap by
  reading the live manifest once and finding 990/1,264 (78%) of ODDS `pending_fetch` rows correlate 1:1 with a MATCHES
  `empty_confirmed` row for the same (date, league) — ODDS was missing the same per-league fixture-calendar completion
  loop PREDICTIONS got in todo #2; fixed with the identical `_captured_leagues` pattern. `instruments-service@e951813`,
  4 new regression tests, full `quality-gates.sh` green, shipped via quickmerge --agent. **Correction (2026-07-12,
  doc-reconciliation finding 256, §A2 "50 reclassified" blanket ruling; was: "This was the last open todo in this doc —
  all 7 todos are now `- [x]`."):** that overclaimed — 5 of the 6 checklist items in this doc are `- [x]`; todo #4
  (re-verify + re-dispatch the footystats backfill VM) remains `- [ ]` BLOCKED-PREREQUISITES below, matching this doc's
  own frontmatter `status: open`. What IS true: todo #4 can now genuinely proceed — all CODE fixes (todos #1, #2, #6)
  are shipped and todo #7's data cleanup is done, so the next dispatch of todo #4 should re-run the typing pass and
  confirm `pending_fetch == 0` for `(footystats, MATCHES)` + `(footystats, PREDICTIONS)` + `(footystats, ODDS)` before
  re-dispatching a backfill VM.
- **2026-07-08** — Todo #7 (reconcile the 20 footystats ODDS `attempted_failed`/phantom rows) FLIPPED (slot-12
  sonnet/high). Data-only fix, no code change — see the todo's own entry above for the full breakdown. Ran
  `scripts/reconcile_phantom_manifest_rows_all.py --asset-group sports --data-types ODDS --unphantom-only` (dry-run
  first, then applied): 19 `phantom_captured_no_parquet_at_canonical_path` rows all had real parquet on disk and flipped
  back to `captured`; the 1 `RuntimeError` row was confirmed genuinely failed (0 blobs at its canonical
  entity=footystats_odds/day= prefix) and left as `attempted_failed` (not a phantom, nothing to reconcile). No commit to
  instruments-service (no code touched, only the live GCS manifest). Todo #6 (extend the write-gate fix to ODDS +
  root-cause the 5-league ongoing gap) remains the only open todo in this doc.
- **2026-07-08** — Todo #4 re-dispatched a SEVENTH time (slot-7 sonnet/high, boot ~22:5x UTC,
  `dispatch_reason: "tier=1 priority=50 plan_order=3 — highest-rank queued task with prereqs met and no collision"`).
  Verified via backlog API: `-003` (ODDS root-cause) flipped to `done` (slot-9, instruments-service@cf89f6061) moments
  after this boot — but slot-9's own Progress Log entry above shows that landing was docs-only and spawned 2 NEW todos
  (#6: extend the confirmed write-gate fix to ODDS + root-cause a separate 5-league ongoing gap; #7: reconcile 20
  `attempted_failed` rows, P3, out of the `pending_fetch` figure so non-gating). Todo #4's own updated un-block note
  (slot-9) says only todo #6 remains before the typing-pass re-verify is meaningful. Neither #6 nor #7 had been ingested
  into the backlog yet (PlanRegenLoop hadn't ticked since slot-9's commit) — ran `POST /api/backlog/regen` (safe,
  additive, PM-plan-derived) to surface them now rather than leave them stranded for another dispatch cycle: 3 new tasks
  appeared, `footystats_matches_predictions_fetch_gaps-005` (todo #6, [CODE] P2, queued/unassigned) and `-006` (todo #7,
  [DATA] P3, queued/unassigned). Not running the typing pass / backfill VM (would only re-confirm the same ODDS residual
  before #6 lands — the same lesson this doc already documents for MATCHES/PREDICTIONS). Releasing `-004` via
  `/skip-current-task` and re-booting so the dispatcher can hand out the now-unblocked `-005` (this slot's craft:
  data_engineering, CODE fix in instruments-service, same write-gate pattern as todo #1 — footystats.py is no longer
  being concurrently edited by slots 8/13, both now `done`).
- **2026-07-08** — Todo #4 re-dispatched a SIXTH time (slot-2 sonnet/high, boot ~22:40 UTC,
  `dispatch_reason: "tier=1 priority=50 plan_order=3 — highest-rank queued task with prereqs met and no collision"`).
  Verified via backlog API: `-002` (PREDICTIONS fixture-calendar) is now `done` (slot-13, instruments-service@78636dd),
  but `-003` (ODDS root-cause, slot-9) is still `dispatched`, not `done` — todo #4's gate ("confirm MATCHES +
  PREDICTIONS + ODDS pending_fetch == 0") requires all three of todo #1/#2/#3; #3 remains open. Not running the typing
  pass / backfill VM (would only re-confirm the already-diagnosed ODDS residual before its code fix, if any, lands). The
  dispatcher-cadence root cause for this repeat re-dispatch is already tracked in
  `plans/active/issues/backlog_blocked_marker_stale_brief_redispatch_2026_07_08.md` (agent-orchestrator,
  backend-engineer craft) — not re-filing. Releasing via `/skip-current-task`; will re-dispatch cleanly once `-003`
  flips to `done`.
- **2026-07-08** — Todo #2 (PREDICTIONS cup fixture-calendar completion) FLIPPED (slot-13 sonnet/high). Mirrored the
  MATCHES `_captured_leagues` + per-league `record_empty(EXPECTED_NO_FIXTURE)` completion pattern into
  `_fetch_footystats_predictions`, replacing the old single date-aggregate empty row with a per-league loop for the
  all-empty branch too. Verified the fix composes correctly with the sibling out-of-subscription write-gate fix
  (`instruments-service@1af6c92`, todo #1) that landed mid-session on the same file — its `continue` guard runs before
  `_captured_leagues.add(...)`, and an out-of-subscription league is also outside `_ft_expected`, so no double-counting.
  Added 2 regression tests. `instruments-service@78636dd`, full `quality-gates.sh` green, shipped via quickmerge
  --agent. Todo #4's un-block sequence now needs only todo #3 (ODDS root-cause) before the typing-pass re-verify makes
  sense.
- **2026-07-08** — Todo #4 re-dispatched a FIFTH time (slot-11 sonnet/high, boot 22:13 UTC,
  `dispatch_reason: "highest-rank queued task with prereqs met and no collision"`). Verified via backlog API: `-002`
  (PREDICTIONS fixture-calendar, slot-13) and `-003` (ODDS root-cause, slot-9) both still `dispatched`, not `done` —
  todo #4's gate remains unmet. Not running the typing pass / backfill VM. Root-caused WHY the BLOCKED-PREREQUISITES
  marker isn't stopping re-dispatch (predicted by slot-8 below as "worth its own issue doc if a 3rd dispatch happens" —
  this is the 4th+ skip since the marker was added) and filed the dedicated dispatcher-bug doc:
  `plans/active/issues/backlog_blocked_marker_stale_brief_redispatch_2026_07_08.md` (repo: agent-orchestrator,
  backend-engineer craft, out of this slot's data_engineering scope — filed + handed off, not fixed inline). Releasing
  via `/skip-current-task`.
- **2026-07-08** — Todo #4 re-dispatched a SECOND time (slot-4 sonnet/high, boot 22:05 UTC,
  `dispatch_reason: "highest-rank queued task with prereqs met and no collision"`) despite the in-doc
  BLOCKED-PREREQUISITES marker slot-8 already added below — the marker text matches the orchestrator's
  `_NON_DISPATCHABLE_RE` taxonomy (`BLOCKED-[A-Z]`) so a future `PlanRegenLoop` prune tick will stop re-offering it, but
  the already-queued DB row from before the marker existed isn't retroactively pruned (prune only touches
  `status=queued AND dispatched_to IS NULL` rows, and this row was still `dispatched` at the time). Re-verified via the
  backlog API (not re-run from scratch): `footystats_matches_predictions_fetch_gaps-002` (PREDICTIONS fixture-calendar)
  = `dispatched` to slot 13, `-003` (ODDS root-cause) = `dispatched` to slot 9 — neither `done` yet, so todo #4's gate
  is still unmet. Not re-running the typing pass / backfill VM (would only reproduce the known residual). Releasing back
  to the queue via `/skip-current-task` rather than looping slot-4 on a task it cannot complete; this slot won't be
  re-offered it again (`slot_skips` exclusion). **If this task gets dispatched a THIRD time before #2/#3 land**, that's
  a P2 dispatcher/regen-prune-cadence issue worth its own issue doc (repo: agent-orchestrator, out of data_engineering
  craft scope) — the `BLOCKED-*` in-text marker taxonomy is doing its job for NEW ingestion, the gap is the orphan-prune
  cadence for a task that was already `dispatched` when the marker was added.
- **2026-07-08** — Todo #4 (re-verify + re-dispatch backfill VM) PARKED with BLOCKED-PREREQUISITES (slot-8 sonnet/high).
  Auto-dispatched immediately after todo #1 closed; boot
  `dispatch_reason: "highest-rank queued task with prereqs met and no collision"` — priority-only dispatch doesn't see
  this todo's in-text dependency on BOTH todo #2 (PREDICTIONS fixture-calendar) and todo #3 (ODDS root-cause), neither
  of which is done. Parked per the established tradfi-plan precedent (in-checkbox marker + un-block sequence) rather
  than re-running the typing pass prematurely (would just reproduce the already-diagnosed PREDICTIONS/ODDS residuals).
  Re-dispatches after todo #2 + #3 land.
- **2026-07-08** — Todo #1 (MATCHES 4-league fetch gap) FLIPPED (slot-8 sonnet/high). See the todo's own entry above for
  the full root-cause + fix writeup. instruments-service@1af6c92.
- **2026-07-08** — Issue filed by slot-14 (data_engineering), dispatched to
  `sports_p2_history_reference_and_odds_2015_to_present-015` (item #7 VERIFY gate). Re-confirmed
  `tm-backfill-20260708-205809` (item #7's TM sub-gate) still RUNNING and healthy (heartbeats + successful club fetches
  in `run.log` as of 21:03 UTC, started 21:00 UTC — too early to expect completion, not stalled). Since item #7 cannot
  flip regardless of the TM VM's outcome until items #4 (understat) and #5 (footystats) also close, and item #5's own
  diagnosis (slot-7, 2026-07-08 20:10 UTC) explicitly recommended filing a dedicated follow-up before further VM spend —
  checked and no such doc existed — filed this issue with 4 actionable todos so a future data_engineering dispatch with
  full session budget can execute the code fixes instead of re-diagnosing from scratch.
- **2026-07-08 (slot-9)** — Dispatched item #4 (re-verify + re-dispatch) first; checked the backlog and found -001
  (MATCHES fix) dispatched to slot 8 and -002 (PREDICTIONS fix) dispatched to slot 13, both still in-progress — item #4
  cannot execute yet (its own done_definition requires those to ship first, and the issue doc explicitly warns a VM
  re-run without the code fix reproduces the identical residual). Skipped -004 back to queue rather than sit idle, and
  the dispatcher handed me -003 (ODDS root-cause) instead — independently scoped, unblocked, no collision with slots
  8/13 (they're editing `footystats.py`; this task is read-only manifest analysis). <br><br>**ODDS root-cause finding**:
  read the live `_index/availability_index.parquet` ONCE (single-walk discipline — this is the consolidated manifest,
  not a corpus walk) and filtered to `(source=footystats, data_type=ODDS)`. `pending_fetch=1,264`
  (`expected_unattempted`) + 20 `attempted_failed` (separate bucket, not in the 1,264 figure). Initial pass (before todo
  #1 landed) found MATCHES, PREDICTIONS, and ODDS all showed `expected_unattempted` for the IDENTICAL leagues on the
  IDENTICAL dates across 10 sampled historical burst dates (2026-03-18, 03-26, 04-15/16, 04-29/30, 05-06/07, 05-27/28),
  suggesting a shared root cause. **After todo #1 landed (instruments-service@1af6c92, slot-8) with the CONFIRMED
  mechanism — a subscription-scope write-gate leak for the 5 `PRED_NO_FOOTYSTATS` leagues (verified via
  `unified-api-contracts/.../league_data_prediction.py`: ARGENTINA_PRIMERA, CHILE_PRIMERA, LIGA_MX, K_LEAGUE_1,
  A_LEAGUE) — re-checked against the actual code**: `_fetch_footystats_odds` (footystats.py ~705-933) never received the
  `if _canonical not in set(_ft_expected): drop` guard todo #1 added to MATCHES/PREDICTIONS
  (footystats.py:198-203/543-548); its write loop (~830-907) has NO subscription-scope check, so it will leak the same 5
  excluded leagues into ODDS coverage. This explains the ~1,087-row historical cluster **for the 3 of those 5 leagues
  that appear in it** (CHILE_PRIMERA, K_LEAGUE_1, ARGENTINA_PRIMERA) but does NOT explain rows for major non-excluded
  leagues (EPL, LA_LIGA, SERIE_A, etc.) also seen in the burst-date sample — that portion's mechanism is still open
  (possibly a shared `/todays-matches` API hiccup on those specific historical dates across all 3 endpoints, since they
  share one bulk call — not yet confirmed, flagged rather than asserted). Separately, an ~177-row **ongoing** daily gap
  (2026-06-01→06-23, near-100% miss) affects 8 leagues: the 3 shared `PRED_NO_FOOTYSTATS` leagues above plus 5 NOT
  subscription-excluded (ALLSVENSKAN, J1_LEAGUE, MLS, ELITESERIEN, BRASILEIRAO, all currently in-season) — this 5-league
  subset is a genuinely separate, unexplained, live gap, not covered by todo #1's mechanism. The remaining 20
  `attempted_failed` rows (`phantom_captured_no_parquet_at_canonical_path` ×19, `RuntimeError` ×1) are a wholly
  separate, already-tooled issue class (`scripts/reconcile_phantom_manifest_rows_all.py` already exists for this) and
  are not part of the 1,264 `pending_fetch` figure at all. <br><br>Filed 2 new actionable todos (item #6: extend todo
  #1's confirmed write-gate fix to ODDS + root-cause the separate 5-league ongoing gap; item #7: run the existing
  phantom-reconciler for the 20 unrelated rows) and revised item #4's park-note so a future re-verify doesn't assume
  ODDS clears purely from todo #6. Flipped item #3's own checkbox — the root-cause ask is answered (partially explained
  by todo #1's confirmed mechanism, partially a distinct, still-open gap, plus one wholly separate known category); did
  not attempt a code fix myself since `footystats.py` was being actively edited by slots 8/13 concurrently (same-file
  collision risk) and todo #1's own fix is the template to extend, not something to duplicate from scratch.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — the sole open todo carries a live
  `BLOCKED-PREREQUISITES` marker (which `_NON_DISPATCHABLE_RE` already excludes from dispatch) and its 2026-07-27
  Progress Log records a genuine REGRESSION that re-blocked it on a NEW doc
  (`footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md`), explicitly instructing 'this
  doc's own checkbox #4 stays `- [ ]` — not flipped'. NOTE for a future pass: the in-checkbox un-block sequence text is
  itself stale (it says 'only todo #6 remains', but #6 is `[x]`); the real blocker is the 2026-07-27 doc. Also
  `execution_scope: orchestrator-agent` contradicts `assigned_vm: NA` — left alone, since Phase 3 only corrects
  `execution_scope` on a RECLASSIFY
- **2026-08-03 (slot-14, data_engineering craft, dispatched via
  `footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md`)**: re-ran the typing pass
  (`type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py` +
  `type_footystats_odds_non_covered_leagues_2026_06_29.py`, both `--apply`, consolidator-merge confirmed) per that doc's
  own todos 1-2 — full details + evidence there. **Still NOT flipping this doc's todo #4** — a genuine residual remains,
  but it is now precisely explained: the live `pending_fetch` remainder (422 rows as of today: 69 MATCHES + 254
  PREDICTIONS + 99 ODDS) is EXACTLY this doc's own todo #1 4-league subscription-exclusion population
  (CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ARGENTINA_PRIMERA — MATCHES and ODDS remainders are precisely these 4 leagues and
  nothing else; PREDICTIONS' remainder is these 4 plus 11 cup/lower-division leagues in the same countries, likely the
  same mechanism). Root cause: todo #1's write-gate fix (`instruments-service@1af6c92`) only stops FUTURE incidental
  `captured` writes — it does not and structurally cannot make the typing scripts' `_covered_leagues_for()` heuristic
  (`≥1 ever-captured row = covered`) forget the historical incidental rows these 4 leagues already accumulated BEFORE
  the fix shipped, so they read "covered" forever and `pending_fetch` grows by a few rows daily with no re-typing pass
  ever able to clear it. This is a NEW understanding beyond what todo #4's own park-note anticipated (it expected a
  one-time re-verify-and-close once #6/#7 landed, not a permanently-regenerating gap) — filed the concrete fix-needed
  todo in the 2026-07-27 doc (`[CODE] P2`, two candidate directions) rather than here, to keep the fix-tracking in one
  place; this doc's todo #4 should stay open/blocked on that new todo, not re-dispatch a bare re-verify again (it would
  just reproduce this same finding).
- **na-eligibility-audit 2026-08-03**: re-read (a new 2026-08-03 Progress Log entry landed since the 07-30 marker;
  `last_updated` frontmatter is stale/unmaintained at 2026-07-27, not a reliable skip signal for this doc). **KEEP-NA
  stands, verdict unchanged.** Sole open todo (#4, re-verify+re-dispatch) still carries its `BLOCKED-PREREQUISITES`
  marker; the 2026-08-03 entry precisely re-explains the residual (422 rows, exactly the 4-league subscription-exclusion
  population) and confirms the real blocker is now the fix tracked in the sibling
  `footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md` doc. NOTE carried over from 07-30
  (still true, not fixed this pass — out of this audit's scope): the in-checkbox un-block sequence text is stale ("only
  todo #6 remains" — #6 is `[x]`).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — verified all still resolve).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — sole open item remains dependency-blocked.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — sole open todo #4 remains genuinely
  `BLOCKED-PREREQUISITES` on `footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md`, which
  is itself still `status: open` with one own open `[DIAG] P3` re-verify todo (not yet flipped) — confirms the same
  dependency-gated verdict `ag_closeout_audit_sports_parked_2026_08_09.md` recorded for this doc today. Note for the
  next pass: the sibling's blocking fix (image rebuild) shipped 2026-08-07 and its re-verify todo's own "done when" (≥2
  consecutive daily 01:30 UTC enumerator runs post-rebuild showing 0 new `pending_fetch`) looks close to satisfied on
  elapsed calendar time alone (today is 2026-08-09, past both the 08-08 and 08-09 01:30 UTC windows) — but that
  verification is the SIBLING doc's own todo to run and flip, not folded in here; not executed this pass (out of this
  doc's own scope, and a live-manifest re-verify is real work, not a citation check).
- **na-eligibility-audit 2026-08-17** [body-hash:2d1aa09a741708c7]: KEEP-NA, stale-items — todo #4's blocker doc independently re-verified resolved (status:resolved, all checkboxes [x]) but deliberately left open pending a VM-dispatch/archived-plan-flip decision per the 2026-08-16 session. Recommend a future pass: cheap re-verify of pending_fetch==0 for footystats MATCHES/PREDICTIONS/ODDS, then close todo #4 + likely archive this doc.
- **context-scout 2026-08-17**: re-verified context_scope (4 entries), unchanged.
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reconfirmed, sole open todo #4 unchanged since the 2026-08-17
  marker. Did not perform the recommended cheap live re-verify (pending_fetch==0 for MATCHES/PREDICTIONS/ODDS) this
  pass — that is a live manifest measurement, not a doc-validity check; leaving the 2026-08-17 recommendation
  standing for whoever next picks this doc up (likely closes todo #4 + archives).
