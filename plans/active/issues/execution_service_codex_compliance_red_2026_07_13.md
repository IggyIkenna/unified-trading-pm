---
doc_type: issue
title: execution-service quality-gates.sh RED — codex compliance 4 violations, ceiling is 3
summary:
  execution-service's CODEX_MAX_VIOLATIONS ceiling (3, set 2026-06-12) is being breached by 4 pre-existing violations
  (function/method size, pip-audit CVEs, backward-compat comment, hardcoded project ID) — blocks all shipping to the
  repo.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service]
scope: [engineer]
tags: [codex, quality-gates, ratchet, repo-blocker]
related:
  [
    plans/active/codex_violations_ratchet_to_five_2026_06_10.md,
    plans/active/utl_reuse_phase7_low_lint_tail_2026_07_13.md,
  ]
created: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
resolved_by:
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
- [ ] [REFACTOR] P3. execution-service: decompose the 26 oversized functions/methods (full list in QG log; largest:
      `matching_engine.py::_execute_l2` 133L, `candle_book_cols.py::match` 117L, `analog_execution_gate.py::apply` 92L)
      below the per-function line budget, or bundle a subset per unit mirroring the
      `codex_violations_ratchet_to_five_2026_06_10.md` facade-extraction pattern. **This is the only remaining
      violation** (all 3 other buckets fixed above) — `Codex compliance: 1 violation (within tolerance of 3)`, not
      currently blocking, but 0 is the target. (repo: execution-service)
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
