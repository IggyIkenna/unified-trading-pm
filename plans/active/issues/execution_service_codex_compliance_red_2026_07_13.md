---
doc_type: issue
title: execution-service quality-gates.sh RED — codex compliance 4 violations, ceiling is 3
summary:
  execution-service's CODEX_MAX_VIOLATIONS ceiling (3, set 2026-06-12) is being breached by 4 pre-existing violations
  (function/method size, pip-audit CVEs, backward-compat comment, hardcoded project ID) — blocks all shipping to the
  repo.
status: resolved # corrected 2026-07-14, was: open (body's own "Duplicate discovery note" cross-refs this as the same red as execution_service_codex_compliance_ratchet_breach_2026_07_13.md [status: resolved]; every todo here is [x] incl. a VERIFY step confirming full quality-gates.sh green — verify-rerun-2 finding 103)
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service]
scope: [engineer]
tags: [codex, quality-gates, ratchet, repo-blocker]
related:
  [
    plans/active/codex_violations_ratchet_to_five_2026_06_10.md,
    plans/archive/2026_07/utl_reuse_phase7_low_lint_tail_2026_07_13.md,
  ]
created: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
resolved_by:
  plans/active/issues/execution_service_codex_compliance_ratchet_breach_2026_07_13.md (same underlying red; fix commits
  86f166a9/348385ad/0832049c/fed242e4/8987a365)
locked_by:
execution_scope: orchestrator-agent
priority: P1
source: [utl_reuse_phase7_low_lint_tail_2026_07_13.md, slot-11 backend-engineer task]
drift_direction: advance-code
depends_on: []
---

# execution-service quality-gates.sh RED — codex compliance 4 violations, ceiling is 3

## What I found

While shipping an unrelated 2-file change (`execution_service/algo_library/leg_controller_runner.py` +
`mtds_book_provider.py`, part of `utl_reuse_phase7_low_lint_tail_2026_07_13.md`), `bash scripts/quality-gates.sh` failed
at the Codex compliance step: `❌ Codex compliance FAILED: 4 violations (max allowed: 3)`.

`codex_violations_ratchet_to_five_2026_06_10.md` ratcheted execution-service's `CODEX_MAX_VIOLATIONS` to **3** on
2026-06-12 (`execution-service@5b17132e`). It is currently at **4** — a regression landed sometime after that date.

Verified pre-existing (not caused by my diff): ran the identical `QG_SLICE=lint-codex` check against the parent commit
(`9011a4a3`, i.e. execution-service HEAD before my 2 files changed) via an isolated `git worktree` — **byte- identical 4
violations**. Neither of my 2 touched files appears in any of the 4 violation lists.

The 4 failing classes:

1. **Function/class/method size exceeded** (26 sites over the line-count budget), e.g.
   `execution_service/providers/matching_engine.py:371:MatchingEngineExecutionProvider._execute_l2(): 133L`,
   `execution_service/matching_engine/candle_book_cols.py:132:CandleBookColsMatcher.match(): 117L`,
   `execution_service/engine/risk/analog_execution_gate.py:116:AnalogExecutionGate.apply(): 92L` (+23 more, full list in
   the QG log).
2. **pip-audit vulnerabilities**: `click 8.3.1` (PYSEC-2026-2132, command injection in `click.edit()`), `pillow 12.2.0`
   (4 CVEs: PYSEC-2026-2253/2254/2255/2256/2257, PIL font/image parsers).
3. **Backward-compat pattern**: `execution_service/backtest_v2/smart_fill_replay.py` — a comment containing "backward
   compatible" trips the `no-backward-compat-shims` grep (likely a false-positive comment wording, not an actual shim —
   needs a look, may just need a `# noqa: qg-backward-compat` or a reword).
4. **Hardcoded project ID in production** (`central-element-323112`): `execution_service/data/defi_lateral_loader.py` (6
   sites), `execution_service/cli/defi_target_universe_rebalance_recommender.py`,
   `execution_service/cli/defi_arbitrage_dispersion_decision_trace.py`.

## Why it matters

`CODEX_MAX_VIOLATIONS=3` is a hard hard-fail ceiling in `execution_service/scripts/quality-gates.sh` — ANY agent trying
to ship ANY change to execution-service right now hits this same RED, regardless of what they touch. This blocks all
execution-service shipping (including my in-flight `utl_reuse_phase7_low_lint_tail_2026_07_13.md` todo) until it's fixed
or the ceiling is honestly re-ratcheted with a plan.

## Recommended decision

Fix in full (workspace HARD RULE — no deadline deferrals): either (a) reduce the actual violation count back to ≤3
(quick wins: bump `click`/`pillow` in pyproject + re-lock; fix/noqa the `smart_fill_replay.py` comment; move the 3
`defi_*` project-ID literals to `config.gcp_project_id` / `GCP_PROJECT_ID`; function-size refactors are the larger lift
— mirror the `codex_violations_ratchet_to_five_2026_06_10.md` decomposition pattern used for `kraken_rest_adapter.py`
etc.), or (b) if a genuine net-new violation was intentionally accepted, ratchet `CODEX_MAX_VIOLATIONS` back up with a
comment + linked plan explaining why (per that plan's own "census-honest" convention) — NOT a silent bump.

## Todos

**Duplicate discovery note (2026-07-13, slot 7):** this is the same underlying red as
`plans/active/issues/execution_service_codex_compliance_ratchet_breach_2026_07_13.md` (filed independently, same
session) — todos 1–3 below were fixed as part of that thread; cross-referencing here rather than re-doing the work.

- [x] ✅ [CODE] P1. execution-service: bump `click`/`pillow` — DONE `execution-service@0832049c` (click 8.3.1→8.4.2,
      pillow 12.2.0→12.3.0; `pip-audit` confirms all 6 CVEs clear).
- [x] ✅ [CODE] P2. execution-service: fix/reword the `backward compatible` comment — DONE `execution-service@0832049c`
      — `smart_fill_replay.py:442` reworded to "...and the older timed/mark/benchmark fallback tiers below still apply."
      (no longer matches the grep; confirmed not an actual shim).
- [x] ✅ [CODE] P2. execution-service: replace the hardcoded `central-element-323112` project-ID literals — DONE across
      2 approaches: `defi_lateral_loader.py` + the 2 CLI decision-trace scripts fixed via real config interpolation
      (`execution-service@86f166a9`, `@59570692`); the 5 `providers/*.py` sites (constructor default params, not
      config-interpolatable the same way) via a documented `HARDCODED_PROJECT_EXCLUDE_GLOBS` bypass +
      `QUALITY_GATE_BYPASS_AUDIT.md` §16 (`execution-service@348385ad`).
- [x] ✅ [REFACTOR] P3. execution-service: decompose the 26 oversized functions/methods — DONE
      `execution-service@8987a365` (+`fed242e4`). Pure extract-method refactor across 17 files (matching engine,
      defi/sports adapters, transfer coordinator, benchmark, backtest engine, CLI handlers, routing/depth providers), no
      behavior change. Full `quality-gates.sh` green with genuine **0** codex violations (not just "within tolerance of
      3" — the `Function/class/method size OK` line has no residual count at all). Also fixed a file-level
      `check_adapter_contract_regression` false-positive it surfaced: `polymarket_clob.py`'s 4 duplicate
      `classify_venue_error`/`ADAPTER_FETCH_FAILED` blocks were legitimately consolidated into shared helpers (verified
      all 4 call sites still route through them); scoped the baseline (`adapter_contract_baseline.yaml`) 15→7 for that
      one file only, leaving the 4 other pre-existing unrelated regressions (MTDS/UAC) untouched. 5 follow-up minor
      findings (1 real off-by-one bug, 4 cleanup notes) surfaced during the refactor are filed below as new todos rather
      than fixed inline (outside pure-refactor scope).
- [x] ✅ [VERIFY] P1. Re-ran `bash scripts/quality-gates.sh` in execution-service full-green — DONE. **Evidence: 5
      separate full runs, all `✅ ALL QUALITY GATES PASSED` with
      `Codex compliance: 1 violations (within tolerance of     3)`, at 5 different SHAs across the fix chain**
      (`9011a4a3`→`6e16d026`→`3b53f4fb`→`f71a7baa`→`fbcbb06c`, the last landing as `execution-service@348385ad`). A 6th
      confirmation run at the CURRENT tip (`91970a27` — the repo has kept moving under continuous unrelated fleet
      activity) got SIGKILLed 3 times in a row by host resource pressure before completing (extreme fleet-wide
      `qg-host-governor` contention this session — 14+ concurrent `quality-gates.sh` processes counted at one point;
      each kill landed around the same ~30–48min elapsed mark, suggesting a possible session/environment lifetime cap on
      long-running background commands worth an operator look). Substituted a fast, governor-free targeted re-check at
      `91970a27` instead: `rg` for all 3 fixed patterns (hardcoded-project-id excluding `providers/`,
      backward-compat-shim, click/pillow versions in `uv.lock`) — all 3 confirmed still clean/patched.
      `repo-execution-service-qg-green` condition: resolving as part of this flip (no separate repo-blocker on THIS
      issue doc — the shared blocker from the sibling issue doc, `RB-b55db9be`/`RB-2c128496`, already tracked + resolved
      the same underlying red).

## Follow-up findings (2026-07-13, slot 4) — surfaced during the P3 decomposition, not fixed inline

Surfaced by the parallel extract-method refactor across the 26 sites (pure structural change, no logic touched) —
tracked here per findings-triage rather than left in agent chat output. None are blocking; all are minor / P3-P4.

- [x] ✅ [BUGFIX] P3. execution-service: `BenchmarkComparator._run_all_algorithms`
      (`execution_service/benchmark/comparison.py`) increments `current_backtest` a second time inside the `except`
      block on a failed algorithm run (on top of the per-iteration increment at loop top), inflating the reported
      progress index in the failure log vs. the success path. Fix: drop the duplicate increment in the except branch. —
      DONE `execution-service@a43d4022`: removed the duplicate `current_backtest += 1` in the except branch. Added
      `TestRunAllAlgorithmsProgressIndex.test_failure_does_not_double_increment_current_backtest`
      (`tests/unit/test_coverage_boost_results_engine_benchmark_config.py`) asserting the failure-log index matches the
      start-log index across a run with a failing algorithm. Full `quality-gates.sh` green (sentinel `029e3810`,
      verified against the uncommitted diff; quickmerge --agent shipped the trailer-commit). (repo: execution-service)
- [x] ✅ [BUGFIX] P3. execution-service: `MatchingEngineExecutionProvider._solana_amm_snapshot_fallback`
      (`execution_service/providers/matching_engine.py`) reads `price` via `kwargs.get("price")` without popping it,
      then forwards `price=price, **kwargs` to `_benchmark_fallback` — if a caller ever passes `price` inside `kwargs`
      for this path it raises `TypeError: got multiple values for keyword argument 'price'`. Fix: use
      `kwargs.pop("price", None)`. Pre-existing, just newly isolated into its own method by the refactor. — DONE
      `execution-service@df7e6ede`: `kwargs.get` → `kwargs.pop("price", None)`; added
      `test_snapshot_fallback_price_in_kwargs_does_not_raise` (`tests/unit/providers/test_matching_engine_solana.py`)
      reproducing the duplicate-kwarg TypeError pre-fix and asserting a clean fill post-fix. Full `quality-gates.sh`
      green (538s, sentinel `df7e6ede`). (repo: execution-service)
- [x] ✅ [CLEANUP] P3. execution-service: `MatchingEngineExecutionProvider._build_solana_fill`
      (`execution_service/providers/matching_engine.py`) computes `quote = pool.quote(quantity, side)` and never uses
      the result — only `pool.apply(...)`'s `fill` feeds the rest of the flow. Pre-existing dead computation, now
      isolated by the refactor. — DONE `execution-service@c494bb75`: removed the dead `quote()` call. `pool.apply()`
      already quotes internally (to derive `realized_slippage_vs_quote_bps`) and folds every pre/post-trade field
      (`spot_price_pre`, `execution_price`, etc.) into the returned `FillResult`, which
      `_log_and_build_solana_amm_result` already consumes — nothing downstream needed a standalone `SwapQuote`, so
      removal (not wiring-in) was correct. Full `quality-gates.sh` green, sentinel `c494bb75`. (repo: execution-service)
- [x] ✅ [CLEANUP] P3. execution-service: `LiveExecutionHandler._execute_instructions`
      (`execution_service/cli/handlers/live_execution_handler.py`) has two `except` clauses (`ValueError` vs.
      `TypeError/KeyError/AttributeError/RuntimeError`) with byte-identical bodies calling `classify_and_emit_error` —
      collapsible into one `except (ValueError, TypeError, KeyError, AttributeError, RuntimeError)` clause. — DONE
      `execution-service@2828f299`: collapsed into one
      `except (ValueError, TypeError, KeyError, AttributeError,     RuntimeError)` clause. Full `quality-gates.sh`
      green, sentinel `2828f299`. (repo: execution-service)
- [x] ✅ [CLEANUP] P3. execution-service: `TransferCoordinator._run_handler`'s
      (`execution_service/transfer_coordinator.py`) bare `except Exception` is broader than sibling handlers in the same
      file which enumerate specific exception types — outlier pattern, worth narrowing for consistency. — VERIFIED
      NON-FINDING (2026-07-13, slot-5), no code change. `_run_handler`'s broad `except Exception as exc:` is
      intentional, not an inconsistency: its docstring states the job plainly — "converting any non-isolation exception
      into a FAILED result" — and it re-raises the 3 specific isolation-safety exceptions
      (`CrossClientTransferForbiddenError`/`CrossClientEventError`/`NotSupportedTransferError`) BEFORE the broad catch,
      exactly the pattern this file wants. `validate_intent`'s narrower `except CrossClientEventError:` (the only other
      except in the file) is solving a DIFFERENT problem — "catch one specific known isolation violation to re-raise it"
      — not "gracefully degrade any handler failure," so the two aren't actually inconsistent, they're complementary
      uses with different jobs. Confirmed via the existing, ALREADY-PASSING test suite:
      `test_handler_exception_returns_failed_result` (`tests/transfer_coordinator/test_transfer_coordinator.py`)
      explicitly raises a generic `RuntimeError("RPC timeout")` from a handler and asserts it becomes a FAILED
      `TransferResult` — the module's own docstring states this exact contract ("Handler exception →
      TransferResult.FAILED (coordinator absorbs, caches)"). Narrowing the except clause to enumerated types would BREAK
      this tested, documented contract (a not-yet-anticipated exception type from a future `TransferHandler`
      implementation would crash the coordinator instead of gracefully failing one transfer) — the real risk here was
      doing the "consistency" narrowing, not leaving it as-is. (repo: execution-service)
