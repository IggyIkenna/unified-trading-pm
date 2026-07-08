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
— fixed in the same commit as the sports/understat manifest-write fix. **Verification note (slot-8 planning, 2026-07-08,
checked after this doc was filed)**: re-ran this exact test on `live-defi-rollout` HEAD `be95c76` — still FAILS
(`assert 'lighter-zksync' in _DEFAULT_EXCHANGES`) — the companion fix described above had not reached LDR as of this
check. Root cause is correctly diagnosed here (rename the assertion string to `"lighter"`); just confirming the fix
commit's landing status for whoever picks up the todos below.

**2 of 3 — ROOT CAUSE FOUND 2026-07-08 (slot-8 planning), NOT the enumerator-side regression this doc originally
suspected — it's a `unified-api-contracts` capability-declaration fix with an unhandled side effect. None of the 3
bisect candidates above (`980f329` / `4a8cff7` / `7ded594`) are the cause; they're all `instruments-service` commits,
but the actual change is in UAC:**

- **Root commit**: `unified-api-contracts@23fa3a99` ("fix(cefi): remove phantom SPOT_PAIR from bare BYBIT/OKX
  INSTRUMENT_TYPES_BY_VENUE", slot-3, 2026-07-07 16:25 UTC+1). This is **NOT an accidental regression** — it's a
  deliberate, production-verified fix (full rationale in the inline comment at
  `unified_api_contracts/registry/venue_constants.py:380-402`): "confirmed against production
  (gs://instruments-store-cefi-prd-.../availability_index.parquet): bare OKX has ZERO SPOT_PAIR rows across its entire
  history ... Tardis's own routing table already sends (OKX, SPOT_PAIR) to the same 'okex' source as canonical OKX_SPOT
  — this entry was a redundant alias, not a distinct real capability." Same rationale for bare BYBIT (2,657 blank +
  legacy-cased rows + 1,193 PERPETUAL-only, zero genuine SPOT_PAIR).
- **BUT it has an unhandled side effect for OKX specifically (BYBIT is fine)**: `BYBIT-SPOT` IS separately declared in
  `VENUES_BY_ASSET_GROUP["cefi"]` (verified: `['BYBIT', 'BYBIT-SPOT']`), so its own EXPECTED tuples resolve directly and
  the golden's `["BYBIT-SPOT", "spot_pair", ...]` entries are UNCHANGED (still present, correctly, at 71 tuples).
  `OKX-SPOT` is **NOT** declared in `VENUES_BY_ASSET_GROUP["cefi"]` (only bare `"OKX"` is — verified via
  `VENUES_BY_ASSET_GROUP['cefi']`), so its `VENUE_DATA_TYPE_CAPABILITIES["OKX-SPOT"]` entry
  (`market_data_categories.py:378`, `{"SPOT_PAIR": ...}`) is orphaned — `build_expected` never iterates a non-declared
  venue. AND `instruments-service`'s `check_enumeration_completeness._CEFI_VENUE_FOLD` still folds manifest `"OKX-SPOT"`
  → `"OKX"` for comparison, so real captured OKX spot rows now compare against `(OKX, spot_pair, *)` — which no longer
  exists post-`23fa3a99`. **Net: real captured OKX spot data is genuinely invisible to both Layer-1 and Layer-2 now** —
  this part IS a real bug, just not the "revert the enumerator" shape originally suspected.
- `test_cefi_okx_spot_folds_to_okx` fails for exactly this reason: it feeds an `OKX-SPOT` manifest row through
  `filter_manifest_to_expected`, which folds it to `OKX` and finds no match.
- **Golden fixture** (`tests/unit/scripts/goldens/expected_universe/cefi.json`, still 75) is simply stale — 71 IS the
  correct current output MINUS the OKX-SPOT hole (i.e. once OKX-SPOT is fixed per below, actual would be 73, still short
  of 75's phantom bare-OKX/BYBIT entries, which really were phantom per the production-verified rationale). **Do NOT
  regenerate to 75** (that WOULD launder the phantom bare-venue tuples back in) — regenerate only after the OKX-SPOT fix
  below lands, expecting 73.

Full duplicate-avoidance cross-reference: this same root cause + fix options are also tracked as a
BLOCKED-OPERATOR-DECISION todo in `cefi_layer1_denominator_gaps_2026_07_03.md` (the plan this drift was discovered
against while verifying task -004) — resolve there or here, not both, and cross out the other when done.

## Why it matters

This blocks `quickmerge --agent` for the ENTIRE instruments-service repo — the sentinel mechanism requires a full green
`quality-gates.sh` run on the exact committed HEAD, and no one currently gets one on `live-defi-rollout` tip without
either fixing this hole or (incorrectly) papering over it via a golden-fixture regen. Per
`codex/02-data/data-pipeline-correctness-hard-rule.md` this is exactly the class of cross-cutting data-correctness break
that freezes downstream shipping until resolved.

## Recommended decision

**BLOCKED-OPERATOR-DECISION** — spans 2 repos + changes the certified cefi denominator, do not guess:

(A) Declare `OKX-SPOT` as its own cefi venue (mirror the `BYBIT-SPOT` precedent already in the same codebase) + remove
`"OKX-SPOT"` from `instruments-service`'s `_CEFI_VENUE_FOLD` so it stops folding to bare `OKX` — **recommended**,
matches the established convention for exchanges with genuinely distinct spot/perp Tardis dialects. Result:
`build_expected('cefi')` → 73 tuples (71 + the 2 real OKX-SPOT tuples), regenerate golden to 73.

(B) Revert `23fa3a99`'s bare-OKX/BYBIT `SPOT_PAIR` removal — re-accepts the fold-target tuples as load-bearing,
contradicting the production-verified rationale that motivated the removal (this would knowingly reintroduce phantom
EXPECTED tuples with zero real captures behind them).

Once decided:

1. Implement the chosen fix (A: `unified-api-contracts` venue declaration + `instruments-service` fold-table edit; or B:
   revert `23fa3a99` in `unified-api-contracts`).
2. Regenerate `tests/unit/scripts/goldens/expected_universe/cefi.json` to match (73 tuples under A, 75 under B) — use
   the docstring recipe in `test_expected_universe_golden.py`, preserving the existing compact one-tuple-per-line JSON
   format (the recipe's raw `json.dump(indent=2)` reformats every entry across 3 lines — reformat back to the checked-in
   single-line-per-tuple style to keep the diff reviewable).
3. Re-run full `quality-gates.sh` on instruments-service to re-establish a green sentinel for `live-defi-rollout` HEAD.

## Todos

- [ ] [DESIGN] P0. **BLOCKED-OPERATOR-DECISION** — decide OKX-SPOT venue declaration (option A, recommended) vs
      reverting the bare-OKX/BYBIT SPOT_PAIR removal (option B) (repo: unified-api-contracts).
- [ ] [FIX] P0. Implement the decided option + regenerate `tests/unit/scripts/goldens/expected_universe/cefi.json` to
      match (repos: unified-api-contracts, instruments-service).
- [ ] [VERIFY] P0. Re-run full `bash scripts/quality-gates.sh` on instruments-service HEAD after the fix to confirm a
      clean green sentinel is re-established for `live-defi-rollout` (repo: instruments-service).
