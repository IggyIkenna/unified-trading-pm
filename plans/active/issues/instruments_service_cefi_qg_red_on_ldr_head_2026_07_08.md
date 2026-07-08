---
doc_type: issue
title:
  instruments-service quality-gates.sh RED on current live-defi-rollout HEAD (be95c76) — CEFI expected-universe drift
  blocks ALL shipping
summary: |
  Full `quality-gates.sh` on instruments-service HEAD (be95c76, a fresh main→LDR backmerge) fails 2 CEFI tests
  unrelated to any in-flight sports/understat work: build_expected('cefi') dropped from 75 to 71 tuples (missing
  BYBIT/OKX spot_pair book_snapshot_5+trades), and the downstream OKX-fold filter test consequently returns 0 rows
  instead of 1. `.qg_last_passed_sha` predates this HEAD — nobody has run a clean full QG on this exact commit yet, so
  this is newly-surfaced, not a known/tracked backlog item. Blocks quickmerge --agent for the WHOLE repo until fixed.
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [cefi, quality-gates, expected-universe, honest-coverage, bybit, okx, regression, ship-blocker]
related: [codex/02-data/availability-manifest-and-data-status.md, codex/02-data/honest-coverage-model.md]
created: 2026-07-08
parent_epic: infrastructure_master
priority: P0
source: slot-7 data_engineering, discovered while shipping understat_local_backfill_completion_2026_07_06.md task -001
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
audited_scope: data-correctness
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-08
locked_since: 2026-05-21
---

# instruments-service quality-gates.sh RED on current HEAD — CEFI expected-universe drift

## What I found

Running the FULL `bash scripts/quality-gates.sh` on instruments-service at current `live-defi-rollout` HEAD
(`be95c76e7986e6050449ac39a86864c8a6767921`, a merge-remote-tracking-branch-'origin/main'-into-_backmerge commit) to
ship an unrelated sports/understat fix, the TESTS stage fails 3 tests. I confirmed via `git stash` that **all 3
reproduce identically with zero diff applied** — this is not caused by any in-flight work, it's the current state of
`live-defi-rollout` itself. `.qg_last_passed_sha` on disk (`7953b540a5c594064c58d3ba47e462e9a72edf44`) predates this
HEAD, meaning **no one has run a clean full QG pass on this exact merged commit yet** — I'm the first to surface this,
not a stale/known backlog item.

**1 of 3 was a stale test, already fixed this session** (see companion fix in this same commit): the docstring/UAC
history shows `unified-api-contracts@f16c79e8` deliberately corrected the LIGHTER-ZKSYNC Tardis exchange slug from
`"lighter-zksync"` to the real Tardis identifier `"lighter"` (confirmed live: `_DEFAULT_EXCHANGES` already contains
`"lighter"`, not `"lighter-zksync"`).
`test_databento_tardis_adapter.py::test_default_exchanges_cover_captured_cefi_venues` just hadn't been updated to match
— fixed in the same commit as the sports/understat manifest-write fix.

**2 of 3 are a genuine, unresolved regression, NOT fixed here — outside my craft-scope/context for this session:**

- `tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[cefi]`:
  `build_expected('cefi')` (in `scripts/expected_universe.py`, delegating through
  `scripts/enumerate_expected_universe.py::_enumerate_v2_cefi`) now returns **71** tuples vs the checked-in golden's
  **75** — missing exactly
  `[('BYBIT', 'spot_pair', 'book_snapshot_5'), ('BYBIT', 'spot_pair', 'trades'), ('OKX', 'spot_pair', 'book_snapshot_5'), ('OKX', 'spot_pair', 'trades')]`.
  The golden was bumped 73→75 by
  `617795b fix(golden): update cefi expected-universe fixture 73→75 tuples (BYBIT-SPOT spot_pair capabilities from UAC@ab6bc7e5)`
  — so these 4 tuples were INTENTIONALLY added once, and something since (candidates from `git log`:
  `980f329 feat(enumerator): v2 cefi/defi/prediction subsume v1 venue-grain PRE_VENUE_LAUNCH sentinel`,
  `4a8cff7 feat(scripts): per-(venue,dt) start_date gate in _enumerate_v2_cefi`,
  `7ded594 feat(enumerator): wire enumerate_expected_universe to UAC TOTAL_UNIVERSE_AXES SSOT`) dropped them back out. I
  have NOT diagnosed which of these three touched the BYBIT/OKX spot_pair path, or whether it's a genuine UAC
  capability-declaration regression vs. an enumerator-side filter regression.
- `tests/unit/scripts/test_filter_manifest_to_expected.py::TestFilterCanonicalisation::test_cefi_okx_spot_folds_to_okx`:
  fails with the SAME symptom — `filter_manifest_to_expected` logs
  `"no manifest triples in EXPECTED — gate would drop every row"` for cefi and returns an empty frame instead of the
  expected 1-row OKX-folded result. Almost certainly the same root cause as the golden drift (EXPECTED is short the
  OKX/BYBIT spot_pair tuples the test fixture relies on).

**Per the test's own docstring warning ("If the change is INTENTIONAL, regenerate the fixture per the docstring
recipe")**: I deliberately did NOT regenerate the golden fixture to match the regressed `actual` output — that would
silently launder a real coverage regression into the new "expected" baseline, which is exactly the failure mode this
golden-byte-identical test exists to catch (per `codex/02-data/honest-coverage-model.md` — the honest-coverage
denominator is read verbatim downstream, never re-derived).

## Why it matters

This blocks `quickmerge --agent` for the ENTIRE instruments-service repo — the sentinel mechanism requires a full green
`quality-gates.sh` run on the exact committed HEAD, and no one currently gets one on `live-defi-rollout` tip without
either fixing this regression or (incorrectly) papering over it via a golden-fixture regen. Per
`codex/02-data/data-pipeline-correctness-hard-rule.md` this is exactly the class of cross-cutting data-correctness break
that freezes downstream shipping until resolved.

## Recommended decision

Need someone with CEFI-enumerator context (not this session's sports/understat scope) to:

1. Bisect which of the 3 candidate commits (`980f329` / `4a8cff7` / `7ded594`) regressed BYBIT/OKX `spot_pair`
   `book_snapshot_5`/`trades` out of `_enumerate_v2_cefi`'s output.
2. Fix the enumerator (or the UAC capability source it reads) so `build_expected('cefi')` produces the 75-tuple set
   again, confirmed against the ALREADY-shipped golden (do not regenerate the golden to match the regression).
3. Re-run full `quality-gates.sh` on instruments-service to re-establish a green sentinel for `live-defi-rollout` HEAD.

## Todos

- [ ] [FIX] P0. Bisect + fix the CEFI v2 enumerator regression dropping BYBIT/OKX spot_pair book_snapshot_5+trades from
      `build_expected('cefi')` (71 vs golden 75 tuples) (repo: instruments-service).
- [ ] [VERIFY] P0. Re-run full `bash scripts/quality-gates.sh` on instruments-service HEAD after the fix to confirm a
      clean green sentinel is re-established for `live-defi-rollout` (repo: instruments-service).
