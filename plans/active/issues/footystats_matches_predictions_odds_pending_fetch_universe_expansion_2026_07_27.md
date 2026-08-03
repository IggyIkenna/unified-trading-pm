---
doc_type: issue
title:
  footystats MATCHES/PREDICTIONS/ODDS pending_fetch regressed to ~35k each — sports canonical universe expansion outran
  the existing non-covered-league typing passes
summary: |
  Filed 2026-07-27 by a data_engineering slot re-checking
  sports_satellite_ao_dispatch_batch4_2026_07_25.md todo #1 ("verify footystats MATCHES/PREDICTIONS/ODDS
  pending_fetch is still 0"). The 2026-07-12 zero-verification (footystats_matches_predictions_fetch_gaps_2026_07_08.md)
  no longer holds: a live single-walk read of `_index/availability_index.parquet` shows
  (footystats, MATCHES) pending_fetch=35,151, (footystats, PREDICTIONS) pending_fetch=35,151,
  (footystats, ODDS) pending_fetch=35,349 — all far from 0. Root-caused (not just reported): this is
  NOT a new code-write-path bug (the 2026-07-08 fixes for MATCHES/PREDICTIONS/ODDS write-gates + fixture-calendar
  completion loops are still correctly in place and unrelated). It is the sports canonical universe
  having expanded to ~300+ additional leagues that footystats does not cover, combined with the
  existing non-covered-league typing scripts (`type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py`,
  `type_footystats_odds_non_covered_leagues_2026_06_29.py`) simply never having been re-run since the
  expansion. Dry-running both scripts live confirms they would re-type 35,106 (MATCHES) + 34,986
  (PREDICTIONS) + 35,278 (ODDS) = 105,370 rows — accounting for ~99.7% of the 105,651-row live
  pending_fetch total across the three data_types. No code fix needed; the fix is re-running
  already-proven-safe existing tooling with --apply.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [footystats, honest-coverage, fetch-gap, pending-fetch-regression, sports-p2, universe-expansion]
related:
  [
    /plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: sports_master
priority: P2
source: sports_satellite_ao_dispatch_batch4-001 (data_engineering slot re-check, 2026-07-27)
assigned_vm: planning
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
depends_on:
supersedes:
superseded_by:
---

## What I found

`sports_satellite_ao_dispatch_batch4_2026_07_25.md` todo #1 asked for a fresh live-manifest re-check of
`footystats_matches_predictions_fetch_gaps_2026_07_08.md`'s todo #4 ("re-verify footystats MATCHES + PREDICTIONS + ODDS
`pending_fetch == 0`"), previously verified 0 on 2026-07-12. A single-walk read of `_index/availability_index.parquet`
(via `unified_trading_library.read_availability_index`, the per-VM-shard-aware consolidated reader — not a raw
single-blob open) scoped to `source=footystats`, `data_type in {MATCHES, PREDICTIONS, ODDS}` shows:

| data_type   | captured | empty_confirmed | expected_unattempted (`pending_fetch`) | attempted_failed |
| ----------- | -------- | --------------- | -------------------------------------- | ---------------- |
| MATCHES     | 30,871   | 248,967         | **35,151**                             | 0                |
| PREDICTIONS | 27,084   | 248,267         | **35,151**                             | 0                |
| ODDS        | 31,203   | 123,025         | **35,349**                             | 4                |

This is NOT zero — the 2026-07-12 verification no longer holds. Per this todo's own instruction ("If the fresh read
instead shows a genuine regression, do NOT silently re-close the checkbox — report the regression as a distinct new
finding"), `footystats_matches_predictions_fetch_gaps_2026_07_08.md`'s own todo #4 checkbox and `status: open` are being
left UNCHANGED (see that doc's own new `## Update (2026-07-27)` Progress Log entry cross-linking here) — this doc is the
actionable follow-up.

**Root cause, confirmed (not assumed):**

1. All `pending_fetch` rows are `date <= today` (2026-07-27) — none are future/not-yet-played fixtures, so this is not
   an artifact of a rolling forward-looking window. `date` spans 2026-02-20 → 2026-07-27.
2. `written_at` for these rows spans 2026-07-13 → 2026-07-27, with a dominant single burst on 2026-07-26 (103,272 of
   ~105,651 rows, `enumerator_run_id=enum-universe-sports-20260726-013031`) — the SAME enumerator run already identified
   in this same batch4 plan's todo #2 finding as the run that leaked legacy `FIXTURES` rows (fixed in
   `instruments-service@ca8bd7b3`, "FIXTURES manifest atom leak in expected-universe enumerator"). That fix only added a
   `FIXTURES` entry to the enumerator's data_type override map — it does not touch MATCHES/PREDICTIONS/ODDS and is NOT
   the cause of this regression.
3. The actual cause: `pending` rows for MATCHES/PREDICTIONS/ODDS are concentrated across **~300 distinct `league_id`
   values** (303 for MATCHES, 295 for PREDICTIONS, 309 for ODDS) that footystats has never returned a single `captured`
   row for — i.e. genuinely non-covered leagues, the exact same class the 2026-07-06/2026-06-29 typing scripts already
   exist to close. Live **dry-run** of both existing scripts (no `--apply`, zero mutation) confirms:
   - `type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py`: 60 MATCHES-covered leagues / 303
     non-covered (35,106 rows to re-type); 51 PREDICTIONS-covered / 295 non-covered (34,986 rows).
   - `type_footystats_odds_non_covered_leagues_2026_06_29.py`: 32 ODDS-covered leagues / 309 non-covered (35,278 rows).
   - Sum: 105,370 rows the existing tooling would close — 99.7% of the 105,651-row live total. The small ~281-row
     remainder is NOT yet root-caused (could be blank-`league_id` rows or a handful of genuinely covered-league gaps) —
     flagged as todo #3 below, not blocking the main fix.
4. This means the underlying WRITE-PATH fixes from `footystats_matches_predictions_fetch_gaps_2026_07_08.md` (todos
   #1/#2/#6 — subscription-scope write-gates + fixture-calendar completion loops) are **not regressed** — they govern
   go-forward writes for the _originally-scoped_ ~62-67-league non-coverage set. What changed is the **denominator**:
   the sports canonical universe grew to include ~300+ additional leagues (consistent with the still-open
   `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` universe-expansion effort) that
   footystats was never subscribed to, and nobody has re-run the non-covered-league typing pass against the new, larger
   universe since 2026-07-12.

## Why it matters

- `sports_p2_history_reference_and_odds_2015_to_present`'s item #5/#7 gate logic (and this batch4 plan's own todo #1)
  depend on this figure reading 0 — a future dispatch that doesn't know this history will either re-diagnose from
  scratch (wasted session) or, worse, wrongly conclude a fetch/backfill VM is needed (wasted compute — the same "VM
  re-run without the typing fix reproduces the residual" lesson the source issue doc already documents for the original
  ~67-league set).
- Left unresolved, this same ~300-league gap will keep regenerating small daily `expected_unattempted` increments (per
  the 18-36 row/day baseline seen 2026-07-13 through 2026-07-25) plus any FUTURE universe expansion bursts, indefinitely
  inflating the "look like a fetch gap" signal when it is actually a known-non-covered-league denominator problem with
  an existing, safe fix.

## Recommended decision

Re-run the two existing, already-proven-safe (dry-run-by-default, additive-only, `captured`-status never touched) typing
scripts with `--apply`, then re-verify. No new code, no VM launch, no delete — this is the same mechanical action
already performed successfully in 2026-07-06/07-12 for the original non-covered-league set.

## Actionable todos

- [x] ✅ [DATA] P2. **Re-run `type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py --apply`** against
      `instruments-store-sports-{env}` with `MANIFEST_PER_VM_SHARDS=true` + a unique `VM_NAME` (per the script's own
      usage block) to re-type the current 35,106 MATCHES + 34,986 PREDICTIONS non-covered- league `expected_unattempted`
      rows to `empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE)`. This is the SAME safe-by-construction script already
      used for this exact purpose in 2026-07-06 — it only ever flips `expected_unattempted`/`attempted_failed` rows for
      leagues with **zero** historical `captured` rows (dynamically computed each run, never hand-maintained), so it
      cannot regress a genuinely-covered league. Confirm the shard lands + the consolidator merges it (or force-merge
      per the existing pattern) before moving to the next todo. (repo: instruments-service, no code change — existing
      script, data-only manifest write). **Done when**: a post-apply live manifest read shows `(footystats, MATCHES)`
      and `(footystats, PREDICTIONS)` `expected_unattempted` counts dropped by ~35,106 / ~34,986 respectively (allow for
      any new daily increment since this doc's filing date). — ✅ **DONE 2026-08-03 (slot-14)**. Dry-run confirmed
      72,749 rows (36,467 MATCHES + 36,282 PREDICTIONS across 306-317 leagues, grown from the filing-date estimate).
      Applied (`VM_NAME=type-fs-mp-slot14-1785730449`): wrote
      `gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/type-fs-mp-slot14-1785730449.parquet`.
      Consolidator merge confirmed (see Progress Log for the lock-stall detour) — post-merge live re-read shows 0
      non-covered-league rows remaining for both data_types.
- [x] ✅ [DATA] P2. **Re-run `type_footystats_odds_non_covered_leagues_2026_06_29.py --apply`** the same way, to re-type
      the current 35,278 ODDS non-covered-league rows. (repo: instruments-service, no code change). **Done when**: a
      post-apply live manifest read shows `(footystats, ODDS)` `expected_unattempted` dropped by ~35,278 (allow for any
      new daily increment). — ✅ **DONE 2026-08-03 (slot-14)**. Dry-run confirmed 36,639 rows / 321 leagues. Applied
      (`VM_NAME=type-fs-odds-slot14-1785730494`): wrote
      `gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/type-fs-odds-slot14-1785730494.parquet`.
      Consolidator merge confirmed; post-merge live re-read shows 0 non-covered-league rows remaining.
- [x] ✅ [DATA] P3. **Root-cause the small remainder** (~281 rows: 105,651 total live pending minus the 105,370 the two
      typing scripts above account for) once the two todos above land — determine if these are blank-`league_id` rows, a
      genuinely-covered-league gap, or another distinct cause; do not assume they clear automatically. (repo:
      instruments-service, read-only manifest analysis). — ✅ **ROOT-CAUSED 2026-08-03 (slot-14)**. Post-merge live
      remainder (grew to 422 rows by today: 69 MATCHES + 254 PREDICTIONS + 99 ODDS — 0 blank `league_id` in all three).
      This is NOT a new/distinct cause — it is the SAME already-diagnosed
      `footystats_matches_predictions_fetch_gaps_2026_07_08.md` todo #1 "4-league subscription-scope incidental-capture"
      bug (CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ARGENTINA_PRIMERA, all genuinely `PRED_NO_FOOTYSTATS`), and it is
      STRUCTURALLY PERMANENT for this typing script's mechanism, not a one-time cleanup gap: MATCHES' remainder is
      EXACTLY those 4 leagues, ODDS' remainder is EXACTLY those 4 leagues, PREDICTIONS' remainder is those 4 plus 11
      more
      (`CHILE_PRIMERA_B, COPA_ARGENTINA, COPA_DO_BRASIL, JLEAGUE_CUP, KOREAN_FA_CUP, K_LEAGUE_2,     LIGA_EXPANSION_MX, NORWEGIAN_CUP, SWISS_CUP, TACA_DA_LIGA, US_OPEN_CUP`
      — cup/lower-division competitions in the same subscription-excluded countries, likely the same mechanism at a
      finer grain). Root cause: todo #1's write-gate fix (`instruments-service@1af6c92`) stops FUTURE incidental
      `captured` writes for these leagues, but each of them already carries historical `captured` rows from BEFORE that
      fix shipped — and this typing script's covered-league determination is `_covered_leagues_for()`: "any league with
      **≥1 ever-captured row**, dynamically computed" (by design, so it never needs hand-maintenance and can't regress a
      genuinely-covered league). That same design means it can **never** un-cover a league once contaminated by even one
      historical incidental row — so these leagues will keep reading "covered" and accumulating fresh daily
      `expected_unattempted` rows FOREVER (dates in this remainder run through TODAY, 2026-08-03), regardless of how
      many times this script is re-applied. New todo filed below (this doc) + cross-referenced in the source doc, since
      fixing this needs a genuine code change (either the expected-universe enumerator excluding subscription-scoped
      leagues at write time, or the typing script's covered-league check going subscription-aware instead of purely
      historical-capture-based), not a data-apply re-run — out of data_engineering craft scope, matching this issue
      chain's own established craft-scope discipline.
- [x] ✅ [DATA] P2. **After the above land, re-verify and close out
      `footystats_matches_predictions_fetch_gaps_2026_07_08.md`'s todo #4** — re-run the same
      `(footystats, MATCHES/PREDICTIONS/ODDS)` `pending_fetch` check this doc's own filing used; if all three genuinely
      read 0 (or the P3 remainder above is itself resolved/re-triaged), flip that doc's todo #4 checkbox + frontmatter
      `status: open` → `status: resolved`, citing this doc's commit + the fresh confirming read. If a genuine residual
      remains, update this doc instead of silently closing it. (repo: unified-trading-pm doc edit). **Done when**:
      `footystats_matches_predictions_fetch_gaps_2026_07_08.md` accurately reflects the final state, one way or the
      other. — ✅ **DONE 2026-08-03 (slot-14)**. A genuine residual remains (todo 3 above) — did NOT flip that doc's
      todo #4 or its `status`. Instead updated that doc's Progress Log with today's findings (typing scripts confirmed
      re-applied + merged; the persisting 422-row residual is the SAME already-diagnosed 4-league bug, now understood to
      be structurally permanent for the dynamic typing-script mechanism, not a re-verify-and-close situation) and
      cross-referenced the new follow-up todo in this doc.
- [ ] [CODE] P2. **NEW, this session (2026-08-03, slot-14).** Fix the structural blind spot found by todo 3 above: the
      footystats non-covered-league typing scripts' `_covered_leagues_for()` (`≥1 ever-captured row = covered`,
      dynamically computed) can never un-cover CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ARGENTINA_PRIMERA (and the 11 related
      PREDICTIONS cup/lower-division leagues) once contaminated by historical incidental `captured` rows written before
      `footystats_matches_predictions_fetch_gaps_2026_07_08.md` todo #1's write-gate fix (`instruments-service@1af6c92`)
      shipped — so `pending_fetch` for these leagues grows by a few rows every day forever, regardless of how many times
      the typing scripts are re-applied. Two candidate fix directions (pick one, repo-owner/backend_engineer judgment
      call, NOT a data-apply task): (a) make the EXPECTED-UNIVERSE ENUMERATOR stop creating new `expected_unattempted`
      rows for footystats-subscription-excluded leagues in the first place (`PRED_NO_FOOTYSTATS` in
      `unified-api-contracts/.../league_data_prediction.py`) — the more structurally correct fix, matching how the
      fetch-loop write gate already works; or (b) make the typing scripts' covered-league determination
      subscription-aware (check `PRED_NO_FOOTYSTATS` directly) instead of purely historical-capture-based, so a one-time
      re-apply can finally clear the ~422-row backlog and any future subscription-excluded league added later doesn't
      repeat this exact blind spot. Repo: instruments-service. Done when: `(footystats, MATCHES/PREDICTIONS/ODDS)`
      `pending_fetch` genuinely reaches (and daily-holds) 0 for these leagues, verified over ≥2 consecutive days
      post-fix (not just one clean read), with a regression test covering the specific "league has historical captured
      rows but is subscription-excluded" case the current heuristic misses.

# Progress Log

- **2026-08-03 (slot-14, data_engineering craft)**: dry-ran both existing typing scripts against the live manifest
  (bounded single-file reads, `scripts/dev/run-bounded-analysis.sh`, 28G cap — the ~250MB/11.85M-row/~20GB-in-memory
  `_index/availability_index.parquet` streams slowly via `gcsfs`, one merge cycle observed at 13m54s), confirmed the
  organic growth since filing (72,749 MATCHES+PREDICTIONS rows / 36,639 ODDS rows, up from the 2026-07-27 estimates of
  ~70,092 / ~35,278), then applied both with unique `VM_NAME`s. **Hit an unrelated infra detour**: the
  `instruments-store-sports-prd` manifest consolidator held its cross-cycle lock for an unusually long time (two
  consecutive slow cycles, 13m54.63s then 12m23.6s, well past this bucket's documented historical max of 8m54s but still
  under its Terraform-set 2400s TTL — `instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`'s known
  failure class) — confirmed via Cloud Run execution history + logs that these were genuine still-running merges, not
  crashed/orphaned locks (each eventually completed successfully with `success=True`), so no manual lock-clear or
  escalation was needed, just a wait. Post-merge live re-reads confirmed both applies landed: 0 non-covered-league rows
  remain for MATCHES/PREDICTIONS/ODDS. Then ran a full live `pending_fetch` breakdown (todo 3) and found the ~422-row
  remainder is entirely the already-diagnosed `footystats_matches_predictions_fetch_gaps_2026_07_08.md` todo #1 4-league
  subscription-exclusion bug, now understood to be STRUCTURALLY PERMANENT for this typing script's
  `_covered_leagues_for()` mechanism (see todo 3's full writeup above) — filed a new `[CODE] P2` follow-up todo in this
  doc rather than attempting the fix myself (needs a real design call between two fix directions, backend_engineer
  craft, not a data-apply task). Did NOT flip `footystats_matches_predictions_fetch_gaps_2026_07_08.md`'s todo #4 —
  updated its Progress Log instead (see that doc). All work shipped as `unified-trading-pm` doc-only commits (no code
  changes this session; the manifest writes went through the existing, already-reviewed typing scripts unmodified).
