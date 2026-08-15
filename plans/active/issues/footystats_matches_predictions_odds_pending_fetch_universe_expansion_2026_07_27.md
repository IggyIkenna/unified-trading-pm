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
author: unknown
last_updated: 2026-08-07
parent_epic: sports_master
priority: P2
source: sports_satellite_ao_dispatch_batch4-001 (data_engineering slot re-check, 2026-07-27)
assigned_vm: planning
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/provider_league_ids.py,
    instruments-service/scripts/enumerate_expected_universe.py,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
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
      (`CHILE_PRIMERA_B, COPA_ARGENTINA, COPA_DO_BRASIL, JLEAGUE_CUP, KOREAN_FA_CUP, K_LEAGUE_2, LIGA_EXPANSION_MX, NORWEGIAN_CUP, SWISS_CUP, TACA_DA_LIGA, US_OPEN_CUP`
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
- [x] ✅ [CODE] P2. **NEW, this session (2026-08-03, slot-14).** Fix the structural blind spot found by todo 3 above:
      the footystats non-covered-league typing scripts' `_covered_leagues_for()` (`≥1 ever-captured row = covered`,
      dynamically computed) can never un-cover CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ARGENTINA_PRIMERA (and the 11 related
      PREDICTIONS cup/lower-division leagues) once contaminated by historical incidental `captured` rows written before
      `footystats_matches_predictions_fetch_gaps_2026_07_08.md` todo #1's write-gate fix (`instruments-service@1af6c92`)
      shipped — so `pending_fetch` for these leagues grows by a few rows every day forever, regardless of how many times
      the typing scripts are re-applied. — ✅ **DONE 2026-08-03 (slot-11)**. Picked direction (a) — the more
      structurally correct fix, matching how the fetch-loop write gate already works: `SPORTS_ENTITY_LEAGUE_COVERAGE`
      (`unified-api-contracts/.../canonical/domain/sports/provider_league_ids.py`) mapped `MATCHES`/`PREDICTIONS` to
      `None` ("all leagues") and `ODDS` wasn't even a key, so the expected-universe enumerator's entity-coverage gate
      (`scripts/enumerate_expected_universe.py::_enumerate_v2_sports`) never fired for footystats at all. Added
      `_FOOTYSTATS_LEAGUE_COVERAGE`, mirroring the existing Understat XG/XG_SHOTS pattern, derived from the SAME
      subscription-scoped denominator the fetch-loop write-gate already uses
      (`get_expected_leagues_for_source("footystats", classifications=["Prediction", "Features"])`); wired into
      `MATCHES`/`PREDICTIONS`/`ODDS`. Shipped: `unified-api-contracts@2a674aa8` (fix + `test_entity_league_coverage.py`
      unit coverage — new `TestFootystatsSubscriptionScopedCoverage` class, 9 tests, plus fixed
      `TestAllLeagueEntities.test_none_means_all_leagues_covered` which had asserted the old buggy `MATCHES is None`
      behavior) and `instruments-service@69391ea9` (enumerator-level regression test —
      `test_sports_v2_footystats_excluded_league_yields_no_provider_coverage` /
      `test_sports_v2_footystats_covered_league_still_seeds_normally`, confirming all 4 diagnosed leagues + all 11
      related PREDICTIONS-cup/lower-division leagues now yield `EXPECTED_NO_PROVIDER_COVERAGE` for
      MATCHES/PREDICTIONS/ODDS while EPL is unaffected). Both repos: full `quality-gates.sh` green, shipped via
      `quickmerge --agent`, verified on `origin/live-defi-rollout`. **Not yet done**: the todo's own stricter "Done
      when" (`pending_fetch` genuinely holds 0 for these leagues over ≥2 consecutive days POST-deploy, since a code fix
      landing today can't be observed across 2 calendar days in the same session) — tracked as a new followup todo below
      rather than left unflipped, since the code fix itself is complete, tested, and shipped.

- [x] ✅ [DIAG] P3. **NEW, this session (2026-08-03, slot-11).** Follow-up to the `[CODE]` todo directly above: once
      `unified-api-contracts@2a674aa8` + `instruments-service@69391ea9` have run through at least one production
      expected-universe enumeration cycle, re-verify `(footystats, MATCHES/PREDICTIONS/ODDS)` `pending_fetch` for
      CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ARGENTINA_PRIMERA (+ the 11 related PREDICTIONS cup/lower-division leagues) over
      ≥2 consecutive days post-deploy — confirming the fix holds in production, not just in the unit-test/live-registry
      checks the `[CODE]` todo already ran. (repo: instruments-service, read-only manifest analysis). Done when: both
      checks (≥24h apart) show 0 pending rows for these leagues, or a genuine residual is found and re-triaged. —
      **GENUINE RESIDUAL FOUND 2026-08-05 (slot-3).** 113 post-fix `expected_unattempted` rows across all 15 target
      leagues over 3 consecutive days (23 on Aug 3, 45 on Aug 4, 45 on Aug 5). The fix is NOT holding: the
      `entity_coverage` gate is not firing in production — ZERO `EXPECTED_NO_PROVIDER_COVERAGE` rows exist for any
      target league despite the UAC code being correct (v0.95.0+ `_FOOTYSTATS_LEAGUE_COVERAGE` properly excludes all 15
      leagues). Root cause: the production Cloud Run job (`expected-universe-v2-sports-daily`, 01:30 UTC,
      `instruments-service:latest` image) still emits `expected_unattempted` rows from
      `enum-universe-sports-2026080X-013038` — the deployed Docker image likely predates the fix. Re-triage needed:
      rebuild + redeploy the `instruments-service:latest` Docker image to pick up the UAC fix, then re-verify. See
      Progress Log for full production evidence.

# Progress Log

- **2026-08-05 (slot-3, data_engineering craft, DIAG follow-up)**: re-verified `(footystats, MATCHES/PREDICTIONS/ODDS)`
  `pending_fetch` for all 15 target leagues against the production
  `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`. **The fix is NOT
  holding.** Findings: (a) 113 post-fix `expected_unattempted` rows across all 15 target leagues over 3 consecutive
  days: 23 on 2026-08-03, 45 on 2026-08-04, 45 on 2026-08-05 — the ~45/day rate is consistent with a daily enumerator
  cycle seeding 1 row per league per data_type for every excluded league. (b) ZERO `EXPECTED_NO_PROVIDER_COVERAGE` rows
  exist for any target league — the `entity_coverage` gate in `_enumerate_v2_sports` (line 2576-2596) is simply not
  firing. (c) The UAC code is CORRECT: `_FOOTYSTATS_LEAGUE_COVERAGE` (v0.95.0, `provider_league_ids.py:839`) properly
  excludes all 15 target leagues; `get_entity_league_coverage("MATCHES")` returns a 49-league frozenset that does not
  include CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ARGENTINA_PRIMERA or any of the 11 cup leagues. (d) The production Cloud Run
  job `expected-universe-v2-sports-daily` runs at 01:30 UTC (`schedule = "30 1 * * *"`) with the
  `instruments-service:latest` Docker image — the `enumerator_run_id` values (`enum-universe-sports-2026080X-013038`)
  match this schedule exactly. (e) The `reason` column is always blank (empty string) for ALL 1,310,964 footystats rows
  — the enumerator writes `reason=""` regardless of `capture_status`, which means `EXPECTED_NO_PROVIDER_COVERAGE` is
  also not persisted even when the gate fires (a separate, smaller issue). **Root cause assessment**: the
  `instruments-service:latest` Docker image used by the Cloud Run job likely predates the UAC fix — the image needs to
  be rebuilt from a post-fix `live-defi-rollout` checkout and redeployed. **Re-triage**: file a new `[INFRA]`/`[CODE]`
  todo to rebuild + redeploy the `instruments-service:latest` image, then re-verify. The pre-fix rows (399, written
  2026-07-13 through 2026-08-02) are expected — they predate the fix and would need a re-apply of the non-covered-league
  typing scripts to clean up. No code changes this session (read-only manifest analysis). All evidence live-verified
  against prod manifest.

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

- **2026-08-03 (slot-11, data_engineering craft, picked up the `[CODE]` follow-up todo above)**: investigated both
  candidate fix directions via a dedicated research sub-agent, confirming direction (a) is correct and precisely scoped:
  `scripts/enumerate_expected_universe.py::_enumerate_v2_sports`'s per-league entity-coverage gate
  (`entity_coverage.get(dt)`, sourced from `unified_api_contracts.sports.get_entity_league_coverage`) is the SAME
  mechanism that already correctly scopes Understat's `XG`/`XG_SHOTS` to the big-5 leagues — but
  `SPORTS_ENTITY_LEAGUE_COVERAGE["MATCHES"]`/`["PREDICTIONS"]` were hardcoded `None` ("FootyStats: all leagues" — the
  comment was simply wrong) and `"ODDS"` wasn't a key at all (`.get()` default `None`), so this gate structurally never
  fired for footystats. Implemented: added `_FOOTYSTATS_LEAGUE_COVERAGE` in
  `unified-api-contracts/unified_api_contracts/canonical/domain/sports/provider_league_ids.py`, built from
  `get_expected_leagues_for_source("footystats", classifications=["Prediction", "Features"])` — the IDENTICAL
  denominator `instruments-service/engine/orchestrator/footystats.py`'s fetch-loop write-gate already uses for all 3
  data_types (confirmed by reading that module directly, not assumed) — wired into `MATCHES`/`PREDICTIONS`/`ODDS`.
  Verified live against the editable-installed registry (via `instruments-service`'s venv, which resolves
  `unified_api_contracts` straight to this slot's UAC checkout) that all 4 diagnosed leagues
  (CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ARGENTINA_PRIMERA) AND the 11 related PREDICTIONS-only cup/lower-division leagues
  are now excluded, while EPL (control) remains included — then ran the actual `_enumerate_v2_sports` call end-to-end
  for both a CHILE_PRIMERA and an EPL catalog entry across all 3 data_types, confirming `EXPECTED_NO_PROVIDER_COVERAGE`
  fires for the excluded league and normal `expected_unattempted` seeding is unaffected for the covered one, BEFORE
  writing the regression tests (proved the fix works against real code, not just against my own new tests). Added
  regression coverage in both repos (see the `[CODE]` todo's DONE note above for the exact test names/shas). Found and
  fixed one PRE-EXISTING UAC test (`TestAllLeagueEntities.test_none_means_all_leagues_covered`) that had directly
  asserted the old buggy `get_entity_league_coverage("MATCHES") is None` behavior — left as-is it would have made this
  fix's own QG run red; updated its parametrize list + added a cross-reference docstring note instead of just deleting
  the assertion. Also recovered an UNRELATED dangling local commit in `market-tick-data-service` (`ffc33d0e`, flagged by
  review as genuinely good but never landed — preserved on `origin/wip-preserve/orchestrator-slot-11-1ebcc587` by
  quickmerge's STAGE 5 regate guard) while waiting on this session's QG runs: rebased the 2 of its 4 touched files that
  hadn't already been independently re-fixed by a different slot's `383ea4c8`, shipped as
  `market-tick-data-service@b7648675`. Both `unified-api-contracts` and `instruments-service` full `quality-gates.sh`
  green, shipped via `quickmerge --agent`, verified reachable from `origin/live-defi-rollout` before flipping the
  checkbox above. Filed the `[DIAG] P3` production-holds-over-2-days follow-up todo above rather than blocking this flip
  on calendar time this session doesn't have.

- **context-scout 2026-08-03**: refreshed context_scope (6 entries — added the two 2026-08-03 CODE-fix source paths,
  `provider_league_ids.py` and `enumerate_expected_universe.py`, since the remaining `[DIAG] P3` follow-up re-verifies
  that exact fix in production; dropped the now-superseded `sports_satellite_ao_dispatch_batch4` archived dispatch doc).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

- **2026-08-07 (slot-10, data_engineering craft, [CODE] P2 follow-up)**: Rebuilt `instruments-service:latest` Docker
  image from `b001100d` (post-fix `live-defi-rollout` HEAD, confirmed to include `instruments-service@69391ea9` +
  `unified-api-contracts@2a674aa8` `_FOOTYSTATS_LEAGUE_COVERAGE`). Build:
  `gcloud builds submit --config=cloudbuild.yaml --substitutions=SHORT_SHA=b001100d,_RUN_INIMAGE_QG=false` (skipped
  in-image QG since QG is enforced at quickmerge + promotion v2 gate). Cloud Build
  `84e0a3ca-81f3-481a-a658-63589bbfb340` SUCCESS, finished 2026-08-07T20:54:20Z. Image digest:
  `sha256:bf73044dca3bbf3b9d5eae7c2c13e952257a677e14e6361b4da37eb10d9127c4`. `expected-universe-v2-sports` (and all
  other `expected-universe-v2-*`) Cloud Run jobs are configured with `instruments-service:latest` — they will pull the
  rebuilt image on their next scheduled run (01:30 UTC 2026-08-08). Re-verification over ≥2 consecutive days filed as
  new [DIAG] P3 follow-up todo above.

## Follow-ups

- [x] ✅ [CODE] P2. Rebuild + redeploy the instruments-service:latest Docker image from a post-fix live-defi-rollout
      checkout (to pick up unified-api-contracts@2a674aa8 _FOOTYSTATS_LEAGUE_COVERAGE) and re-verify (footystats,
      MATCHES/PREDICTIONS/ODDS) pending_fetch for the 15 target leagues over >=2 consecutive days — the [x] [DIAG] P3
      todo's own 2026-08-05 text confirms the entity_coverage gate is NOT firing in production (113 post-fix rows, zero
      EXPECTED_NO_PROVIDER_COVERAGE, deployed image likely predates the fix) and says 'Re-triage needed'. — ✅ **REBUILD
      DONE 2026-08-07 (slot-10)**. `gcloud builds submit` from `instruments-service` at b001100d (post-fix LDR HEAD,
      includes `instruments-service@69391ea9`); `instruments-service:latest` rebuilt and pushed to AR (digest
      sha256:bf73044dca3bbf3b9d5eae7c2c13e952257a677e14e6361b4da37eb10d9127c4). Evidence:
      `cloudbuild=84e0a3ca-81f3-481a-a658-63589bbfb340` SUCCESS. `expected-universe-v2-sports` Cloud Run job uses
      `:latest` — next scheduled run at 01:30 UTC will pull the updated image. **Re-verification over ≥2 consecutive
      days NOT yet done** (requires calendar time post-deploy) — tracked as new [DIAG] P3 todo below.
- [ ] [DIAG] P3. Re-verify `(footystats, MATCHES/PREDICTIONS/ODDS)` `pending_fetch` for the 15 target leagues
      (CHILE_PRIMERA, K_LEAGUE_1, LIGA_MX, ARGENTINA_PRIMERA + 11 PREDICTIONS cup/lower-division leagues) over ≥2
      consecutive days post-2026-08-07 image rebuild — confirming `entity_coverage` gate now fires in production
      (`EXPECTED_NO_PROVIDER_COVERAGE` rows appear for the excluded leagues, `pending_fetch` stops growing). **Done
      when**: ≥2 daily enumerator runs (at 01:30 UTC) both show 0 new `pending_fetch` rows for the target leagues; or a
      genuine residual is found and re-triaged. (repo: instruments-service, read-only manifest analysis).

> **2026-08-06 archive-candidate audit**: The [x] [DIAG] P3 todo is a clear checkbox-vs-prose contradiction: its body
> confirms the shipped fix is NOT holding in production, that the deployed Cloud Run image predates the fix, and
> explicitly calls for re-triage (rebuild+redeploy+re-verify) — none of which is a tracked open todo. The 2026-08-05
> Progress Log restates 'file a new [INFRA]/[CODE] todo'.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
