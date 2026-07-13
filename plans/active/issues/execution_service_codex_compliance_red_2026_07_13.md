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

- [ ] [CODE] P1. execution-service: bump `click` to ≥8.3.2 and `pillow` to ≥12.3.0 in pyproject.toml, re-lock, re-verify
      no API breakage (pip-audit class). (repo: execution-service)
- [ ] [CODE] P2. execution-service: fix/reword the `backward compatible` comment in
      `execution_service/backtest_v2/smart_fill_replay.py` (or add `# noqa: qg-backward-compat` if it's a false positive
      — confirm it's not an actual compat shim first). (repo: execution-service)
- [ ] [CODE] P2. execution-service: replace the 3 hardcoded `central-element-323112` project-ID literals in
      `execution_service/data/defi_lateral_loader.py` +
      `execution_service/cli/defi_target_universe_rebalance_recommender.py` +
      `execution_service/cli/defi_arbitrage_dispersion_decision_trace.py` with `config.gcp_project_id` /
      `resolve_bucket_name(...)`. (repo: execution-service)
- [ ] [REFACTOR] P3. execution-service: decompose the 26 oversized functions/methods (full list in QG log; largest:
      `matching_engine.py::_execute_l2` 133L, `candle_book_cols.py::match` 117L, `analog_execution_gate.py::apply` 92L)
      below the per-function line budget, or bundle a subset per unit mirroring the
      `codex_violations_ratchet_to_five_2026_06_10.md` facade-extraction pattern. (repo: execution-service)
- [ ] [VERIFY] P1. Once the above land, re-run `bash scripts/quality-gates.sh` in execution-service full-green, confirm
      `CODEX_MAX_VIOLATIONS=3` holds (or ratchet honestly if a residual is accepted), then flip the
      `repo-execution-service-qg-green` condition / resolve the repo-blocker. (repo: execution-service)
