---
doc_type: issue
title:
  "market-tick-data-service QG RED at LDR HEAD — 2 pre-existing test failures (fleet-blocking); slot-12 gas_fee diff
  coverage-verified green (80.63%)"
summary: >-
  quality-gates.sh on market-tick-data-service at LDR HEAD is RED on 2 unit tests, verified PRE-EXISTING on a clean tree
  (stash removed): test_collect_handler_schema.py::TestCollectHandlerCoversProtocolClass::
  test_protocol_class_ops_have_modules[lending] and test_orchestrator_per_data_type_sentinel.py::
  test_tier3_prediction_polymarket_no_crash. Suite: 9987 passed / 2 failed / 25 skipped / 1 xpassed. Coverage on the
  CLEAN tree PASSES (80.65% ≥ 79% gate). CORRECTION (authoritative full-run, 2026-08-05): the earlier Pass-1-with-diff
  "76.21%" + "3rd failure" reading was a TRUNCATED-RUN artifact (aster WS flaky failure cut the suite → partial,
  non-comparable coverage). The full quality-gates.sh run WITH slot-12's gas_fee diff: 9988 passed / 2 failed / 25
  skipped / 1 xpassed, coverage 80.63% — PASSES the 79% gate (−0.02pt vs clean). slot-12's diff is coverage-green; the
  P2 "restore coverage" obligation is DISMISSED. The ONLY remaining blockers are the same 2 pre-existing test failures
  (P1), owned by the UAC-side removal decision (see mtds_qg_red_uac_capability_declaration_drift_2026_08_05). slot-12
  declares a repo-blocker (qg_red) for the 2 pre-existing failures.
status: open
nature: issue
asset_group: [cefi, defi, sports, tradfi]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [red-tree, qg, test-failure, fleet-blocking, coverage]
related:
  [
    plans/active/issues/features_gas_fees_calculator_stale_legacy_venue_read_2026_07_30.md,
    plans/active/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-05
author: unknown
last_updated: 2026-08-05
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: [data_engineering slot-12, 2026-08-05 — task features_gas_fees_calculator_stale_legacy_venue_read-002]
resolved_by:
context_scope:
  [
    market-tick-data-service/tests/unit/test_aster_ws_connector.py,
    market-tick-data-service/tests/unit/test_orchestrator_per_data_type_sentinel.py,
    market-tick-data-service/tests/unit/test_collect_handler_schema.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/gas_fee_handler.py,
    market-tick-data-service/tests/unit/test_gas_fee_handler.py,
    market-tick-data-service/tests/unit/test_gas_fee_handler_coverage.py,
  ]
---

# market-tick-data-service QG RED at LDR HEAD (fleet-blocking)

> **Filed by**: data_engineering slot-12, 2026-08-05, per worker.md §4b (blocked ON THE REPO, not my task). Slot-12's
> unrelated gas_fee work (dead-code removal for
> `plans/active/issues/features_gas_fees_calculator_stale_legacy_venue_read_2026_07_30.md` P3) cannot ship under the
> green-tree rule until this repo is green.

## What I found

While shipping the gas_fee P3 dead-code removal, Pass-1 `quality-gates.sh` on market-tick-data-service at LDR HEAD came
back RED. A clean-tree verification QG (slot-12's diff stashed, LDR HEAD) established exactly what is pre-existing:

1. **2 unit tests FAIL on a clean tree** (verified pre-existing, byte-identical):
   - `test_collect_handler_schema.py::TestCollectHandlerCoversProtocolClass::test_protocol_class_ops_have_modules[lending]`
   - `test_orchestrator_per_data_type_sentinel.py::test_tier3_prediction_polymarket_no_crash` Suite on clean tree:
     `9987 passed, 2 failed, 25 skipped, 1 xpassed`. Lint / codex / typecheck pass.
2. **Coverage PASSES on a clean tree** — `Required test coverage of 79.0% reached. Total coverage: 80.65%`. The repo
   runs `[tool.coverage.run] branch=true`, so the gate is the COMBINED line+branch measure; the clean tree clears it.
3. **CORRECTION to the earlier Pass-1 assessment (2026-08-05, slot-12, post-full-QG)**: the Pass-1-with-diff run showed
   76.21% coverage + a 3rd failure
   (`test_aster_ws_connector.py::TestAsterBook::test_stream_yields_real_depth5_tick_via_inherited_binance_parser`). A
   FULL quality-gates.sh run WITH slot-12's diff applied now proves BOTH were an artifact of a TRUNCATED pytest run: the
   aster WS test failed mid-suite, which cut the suite short and produced a PARTIAL coverage figure (the terminal % on a
   partial run is not comparable to the full-suite gate). The full run with the diff: **9988 passed / 2 failed / 25
   skipped / 1 xpassed, coverage 80.63% — PASSES the 79% gate** (vs 80.65% clean, −0.02pt). So slot-12's gas_fee
   dead-code removal does NOT drop coverage below the gate; the P2 coverage obligation is DISMISSED (diff ships green on
   coverage). The ONLY remaining blockers are the same 2 pre-existing test failures (P1).

## Why it matters

- **Fleet-blocking under the green-tree rule**: the 2 pre-existing test failures fail the commit boundary and quickmerge
  Pass-1/Pass-2, so NO market-tick-data-service commit can ship until they are fixed/stabilized. This blocks every
  in-flight MTDS worker, not just slot-12.
- The `[lending]` protocol-class failure suggests the handler-module mapping (e.g. `_CLI_OP_TO_MODULE` style) may have
  drifted for the lending class — a real consistency signal worth checking while fixing.
- Slot-12's gas_fee P3 (dead-code removal) is held ONLY by the pre-existing red — its own coverage is verified green
  (80.63% with the diff applied, P2 dismissed); it ships the moment the repo is green.

## Recommended decision

1. Fix the 2 pre-existing MTDS test failures (top MTDS priority, P0) so the repo unblocks fleet-wide.
2. (DISMISSED — not needed) Coverage with slot-12's gas_fee diff applied is 80.63%, PASSING the 79% gate; the earlier
   "76.21%" figure was a truncated-run artifact. No compensating tests needed; the diff is coverage-green.
3. Re-verify CI on LDR is green before further MTDS ships resume.

## Todos

- [ ] [DATA] P1. Fix the 2 pre-existing failing unit tests in market-tick-data-service (collect_handler_schema
      `[lending]` protocol-class ops, orchestrator tier3_polymarket no-crash sentinel): flaky-vs-real, then stabilize or
      fix. Unblocks all MTDS commits fleet-wide. (repo: market-tick-data-service)
- [x] [DATA] P2. (slot-12) Confirm market-tick-data-service combined coverage stays ≥79% WITH the gas_fee
      dead-code-removal diff applied. **DISMISSED by full-run measurement**: the authoritative full quality-gates.sh run
      WITH the diff is 80.63% (PASSES, vs 80.65% clean, −0.02pt); the earlier "76.21% drop" was a truncated-run artifact
      (aster flaky failure cut the suite → partial coverage). No compensating tests needed. — **Done 2026-08-05**,
      evidence: full QG run `/tmp/qg_with_diff.log`, coverage.xml 80.63%. (repo: market-tick-data-service)

## Progress Log

- **2026-08-05 (data_engineering slot-12)**: found while shipping the gas_fee P3 dead-code removal. Pass-1-with-diff QG
  red (coverage 76.21% + 3 tests). Clean-tree verification QG at LDR HEAD (stash@{0} removed) → **corrected picture**:
  coverage 80.65% PASSES clean; 2 test failures are pre-existing; aster was flaky; the coverage shortfall was slot-12's
  own diff. Declared repo-blocker RB (mtds qg_red) for the 2 pre-existing failures. Slot-12's diff is in the
  **`market-tick-data-service` WORKING TREE** (3 files: `cli/handlers/gas_fee_handler.py`,
  `tests/unit/test_gas_fee_handler.py`, `tests/unit/test_gas_fee_handler_coverage.py`), NOT shipped; P3 checkbox NOT
  flipped. Restoring coverage is slot-12's in-flight obligation (P2 todo above).
- **2026-08-05 (data_engineering slot-12) RB GREEN — UAC-side resolution shipped**: the 2 pre-existing failures are
  resolved by the operator-ruled UAC-side removals at `unified-api-contracts@5f441e0d` (AAVE `collect-rewards` +
  POLYMARKET `fills` declarations removed — see `mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md`). This is
  the repo-blocker unblock: MTDS re-gate (full `bash scripts/quality-gates.sh` WITH slot-12's gas_fee diff) started
  ~14:04Z, log `/tmp/qg_green_ship.log`; editable-install now includes `5f441e0d`, so both failures should clear. **On
  green**: ship slot-12's 3 code files via `quickmerge --agent --files`, flip the P3 checkbox in
  `features_gas_fees_calculator_stale_legacy_venue_read_2026_07_30.md` same-turn, verify SHA on origin, POST /done.
- **2026-08-05 (data_engineering slot-12) PUSH-BLOCKED NOTE**: this issue doc could NOT be pushed via quickmerge at
  filing time. PM quickmerge ran the FULL gate (not prek-only) because a concurrent session's live edit to
  `plans/active/issues/dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md` (mtime 12:54) dirtied the tree;
  the full gate then failed on the PRE-EXISTING `agent-rules-size-cap` check — `cursor-configs/CLAUDE.md` is 41,008 B,
  48 B over the 40,960 B hard cap (committed at HEAD 0606cf330, 2026-08-05 11:51). Clean-tree `docs(plans:)` commits run
  prek-only and bypass this check, so the PM gate red does NOT block ordinary plan-flips — it only blocks FULL-gate PM
  agent commits. Recommend (separate small finding): condense 48 B out of `cursor-configs/CLAUDE.md` to restore the cap;
  do NOT raise the cap.
- **2026-08-05 (data_engineering slot-12) COVERAGE CORRECTION**: ran the FULL quality-gates.sh WITH the gas_fee diff
  applied (`/tmp/qg_with_diff.log`, exit 1 only on the 2 pre-existing failures). Result: 9988 passed / 2 failed,
  coverage **80.63% PASSES** the 79% gate (clean baseline 80.65%, −0.02pt; coverage.xml: 22141/26474 lines + 5798/8176
  branches = 80.63% combined). The earlier 76.21% Pass-1-with-diff figure was a TRUNCATED-RUN artifact — the aster WS
  test failed mid-suite, cutting the run short and producing a partial (non-comparable) coverage percentage. The P2
  "restore coverage" obligation is DISMISSED as a non-issue; the diff is coverage-green. NOTE this corrects the prior
  Pass-1 claim in this doc AND the "coverage drop ~4.4pts" text in
  `features_gas_fees_calculator_stale_legacy_venue_read_2026_07_30.md`'s Progress Log (2026-08-05 entry).
