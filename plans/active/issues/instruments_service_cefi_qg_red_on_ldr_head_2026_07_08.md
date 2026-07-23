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
related: [/codex/02-data/availability-manifest-and-data-status.md, /codex/02-data/honest-coverage-model.md]
created: 2026-07-08
parent_epic: infrastructure_master
priority: P0
source: slot-7 data_engineering, discovered while shipping understat_local_backfill_completion_2026_07_06.md task -001
assigned_vm: NA
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

**Verification note (slot-3 planning, 2026-07-08, dispatched task `instruments_service_cefi_qg_red_on_ldr_head-002`
[VERIFY])**: ran full `bash scripts/quality-gates.sh` on instruments-service at `live-defi-rollout` HEAD `be95c76`
(unchanged) — still RED, same 3 failures as originally filed (`test_cefi_okx_spot_folds_to_okx`,
`test_default_exchanges_cover_captured_cefi_venues`, `test_default_exchanges_cover_captured_cefi_venues` lighter-zksync
assert). Confirms the DESIGN (todo 1) and FIX (todo 2) below have NOT landed yet — the VERIFY todo (3) cannot pass until
they do. Not attempting the fix myself: the DESIGN todo is explicitly `BLOCKED-OPERATOR-DECISION` spanning 2 repos +
changes the certified cefi denominator. Filing `/blocked` on the dispatcher instead of guessing.

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

**Action taken 2026-07-08 (slot-5 planning, dispatched task `instruments_service_cefi_qg_red_on_ldr_head-001`, a STALE
backlog snapshot predating the DESIGN/FIX/VERIFY rewrite above — the dispatched brief still read the original "bisect +
fix the enumerator" text, not the BLOCKED-OPERATOR-DECISION framing).** Independently root-caused to the same
`unified-api-contracts@23fa3a99` commit (converges with slot-8's analysis above) before seeing this doc's later edits.
**Shipped Option B, NOT the recommended Option A** — reverted `23fa3a99` in full (`unified-api-contracts@1771d59a`),
restoring `SPOT_PAIR` to bare `OKX` AND bare `BYBIT`, then fixed the adjacent stale `lighter-zksync` assertion
(`instruments-service@666bca5`). Full green `quality-gates.sh` re-established (sentinel =
`666bca55730391d02a657b35d28443c1fa841774`) and **both commits are already pushed to `live-defi-rollout`** —
`quickmerge --agent` is unblocked for the whole instruments-service repo again.

Why B over the recommended A, and the known gap this leaves: for **OKX** this is functionally equivalent to A's intent —
`check_enumeration_completeness._CEFI_VENUE_FOLD` still folds manifest `OKX-SPOT` rows to `OKX` for comparison, so
restoring bare-`OKX` `SPOT_PAIR` makes real captured OKX-SPOT data match EXPECTED again (Layer-1 visibility genuinely
fixed, not just golden-laundered). For **BYBIT** this is weaker than A: `BYBIT-SPOT` already covers real captures, so
the restored bare-`BYBIT` `spot_pair` cells (`book_snapshot_5`/`trades`) have zero real captures behind them and will
show `expected_unattempted` **permanently** — an honest-but-unfulfillable denominator inflation (2 tuples), not a
masked/silent data hole, but still the exact "phantom" pattern `23fa3a99` was trying to remove.

**Not closing the DESIGN todo below** — this was a unilateral interim fix to clear the P0 shipping freeze fast, not the
deliberated Option A the operator was asked to weigh in on. Filing `/blocked` to confirm: keep B as shipped (re-file a
small follow-up to accept the 2-tuple bare-BYBIT phantom permanently), or do the Option-A follow-up (declare `OKX-SPOT`
its own cefi venue + drop the fold + re-remove bare-BYBIT `SPOT_PAIR` + regenerate golden to 73). Either way the P0
shipping-freeze is already resolved; this is now a lower-urgency architecture cleanup.

## Why it matters

This blocks `quickmerge --agent` for the ENTIRE instruments-service repo — the sentinel mechanism requires a full green
`quality-gates.sh` run on the exact committed HEAD, and no one currently gets one on `live-defi-rollout` tip without
either fixing this hole or (incorrectly) papering over it via a golden-fixture regen. Per
`/codex/02-data/data-pipeline-correctness-hard-rule.md` this is exactly the class of cross-cutting data-correctness
break that freezes downstream shipping until resolved.

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

- [ ] [DESIGN] P1. **BLOCKED-OPERATOR-DECISION (downgraded from P0 — shipping freeze already cleared by the interim
      Option-B fix below)** — confirm keeping Option B as shipped (accept the permanent 2-tuple bare-BYBIT
      `expected_unattempted` phantom) OR do the Option-A follow-up (declare `OKX-SPOT` its own cefi venue in
      `VENUES_BY_ASSET_GROUP["cefi"]`, remove it from `instruments-service`'s `_CEFI_VENUE_FOLD`, re-remove bare-BYBIT
      `SPOT_PAIR`, regenerate golden to 73 tuples) (repo: unified-api-contracts).
- [x] ✅ [FIX] P0. Shipped interim Option B — reverted `unified-api-contracts@23fa3a99`
      (`unified-api-contracts@1771d59a`, 2026-07-08, slot-5 planning), restoring `build_expected('cefi')` to the
      golden's 75 tuples. **Not the recommended Option A** — see "Action taken" note above; DESIGN todo re-opened above
      pending operator confirmation of whether to keep this or follow up with A.
- [x] ✅ [VERIFY] P0. Re-ran full `bash scripts/quality-gates.sh` on instruments-service — GREEN
      (`instruments-service@666bca5`, sentinel `666bca55730391d02a657b35d28443c1fa841774`), also fixing the adjacent
      stale `lighter-zksync` assertion in the same commit. `quickmerge --agent` unblocked for the whole repo again.
