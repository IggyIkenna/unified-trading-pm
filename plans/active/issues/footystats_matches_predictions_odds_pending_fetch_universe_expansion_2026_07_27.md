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
    /plans/active/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
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

- [ ] [DATA] P2. **Re-run `type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py --apply`** against
      `instruments-store-sports-{env}` with `MANIFEST_PER_VM_SHARDS=true` + a unique `VM_NAME` (per the script's own
      usage block) to re-type the current 35,106 MATCHES + 34,986 PREDICTIONS non-covered- league `expected_unattempted`
      rows to `empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE)`. This is the SAME safe-by-construction script already
      used for this exact purpose in 2026-07-06 — it only ever flips `expected_unattempted`/`attempted_failed` rows for
      leagues with **zero** historical `captured` rows (dynamically computed each run, never hand-maintained), so it
      cannot regress a genuinely-covered league. Confirm the shard lands + the consolidator merges it (or force-merge
      per the existing pattern) before moving to the next todo. (repo: instruments-service, no code change — existing
      script, data-only manifest write). **Done when**: a post-apply live manifest read shows `(footystats, MATCHES)`
      and `(footystats, PREDICTIONS)` `expected_unattempted` counts dropped by ~35,106 / ~34,986 respectively (allow for
      any new daily increment since this doc's filing date).
- [ ] [DATA] P2. **Re-run `type_footystats_odds_non_covered_leagues_2026_06_29.py --apply`** the same way, to re-type
      the current 35,278 ODDS non-covered-league rows. (repo: instruments-service, no code change). **Done when**: a
      post-apply live manifest read shows `(footystats, ODDS)` `expected_unattempted` dropped by ~35,278 (allow for any
      new daily increment).
- [ ] [DATA] P3. **Root-cause the small remainder** (~281 rows: 105,651 total live pending minus the 105,370 the two
      typing scripts above account for) once the two todos above land — determine if these are blank-`league_id` rows, a
      genuinely-covered-league gap, or another distinct cause; do not assume they clear automatically. (repo:
      instruments-service, read-only manifest analysis).
- [ ] [DATA] P2. **After the above land, re-verify and close out
      `footystats_matches_predictions_fetch_gaps_2026_07_08.md`'s todo #4** — re-run the same
      `(footystats, MATCHES/PREDICTIONS/ODDS)` `pending_fetch` check this doc's own filing used; if all three genuinely
      read 0 (or the P3 remainder above is itself resolved/re-triaged), flip that doc's todo #4 checkbox + frontmatter
      `status: open` → `status: resolved`, citing this doc's commit + the fresh confirming read. If a genuine residual
      remains, update this doc instead of silently closing it. (repo: unified-trading-pm doc edit). **Done when**:
      `footystats_matches_predictions_fetch_gaps_2026_07_08.md` accurately reflects the final state, one way or the
      other.
