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
- [ ] [CODE] P2. **Extend the confirmed subscription-scope write-gate fix (todo #1, instruments-service@1af6c92) to
      ODDS, plus root-cause a separate 5-league gap ODDS alone shows** — investigation (slot-9, 2026-07-08, see Progress
      Log) confirms `_fetch_footystats_odds` (footystats.py ~line 705-933) never received the write-gate guard todo #1
      added to MATCHES/PREDICTIONS (`if _canonical not in set(_ft_expected): drop`, footystats.py:198-203/543-548) — its
      per-league write loop (~line 830-907) writes ANY league present in the API response as `captured` with no
      subscription-scope check at all. The 5 `PRED_NO_FOOTYSTATS`-excluded leagues (confirmed via
      `unified-api-contracts/.../league_data_prediction.py`: ARGENTINA*PRIMERA, CHILE_PRIMERA, LIGA_MX, K_LEAGUE_1,
      A_LEAGUE) will leak into ODDS coverage the exact same way MATCHES/PREDICTIONS did pre-fix — apply the identical
      guard here. **Separately**, ODDS shows an ~177-row \_ongoing* daily gap (2026-06-01→06-23, near-100% miss) for 8
      leagues, only 3 of which (CHILE_PRIMERA, K_LEAGUE_1, ARGENTINA_PRIMERA) are `PRED_NO_FOOTYSTATS`-excluded — the
      other 5 (ALLSVENSKAN, J1_LEAGUE, MLS, ELITESERIEN, BRASILEIRAO) are NOT subscription-excluded and are NOT
      explained by todo #1's confirmed mechanism; all 5 are currently in-season, so this is a live, unexplained,
      undiagnosed gap needing its own investigation (repo: instruments-service).
- [ ] [DATA] P3. **Reconcile the 20 footystats ODDS `attempted_failed`/`phantom_captured_no_parquet_at_canonical_path`
      rows** — a DISTINCT, already-known issue class (manifest says an attempt was made but the parquet write is missing
      at the canonical path), NOT part of the `pending_fetch=1,264` figure (these are `attempted_failed`, not
      `expected_unattempted`) and NOT related to the write-gate root cause above. Existing tooling already handles this
      pattern (`scripts/reconcile_phantom_manifest_rows_all.py`, `scripts/dedup_phantom_after_recovery.py`) — run the
      existing reconciler scoped to `(source=footystats, data_type=ODDS)` rather than writing new code (repo:
      instruments-service).

## Progress Log

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
