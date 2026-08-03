---
doc_type: plan
title: Test-impact / selective execution — fleet-wide eligibility measurement, then staged rollout
summary: >-
  Extends a 4-repo commit-classification sample (execution-service, features-service, instruments-service,
  market-data-processing-service) to all ~23 Python fleet repos, to turn the selective-test-execution design's savings
  estimate from a guess into a real, per-repo measured number — then stages the design's own already-scoped
  implementation rollout (walker, allowlists, golden-set tests, single-repo shadow trial, fleet trial, promotion) behind
  an explicit operator-review gate. Phase 1 (measurement) is immediately actionable; Phase 2 (implementation) is
  BLOCKED-OPERATOR-DECISION until the design doc's own review todo closes.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, execution-service, features-service, instruments-service, market-data-processing-service]
scope: [engineer]
tags: [ci-cd, testing, pytest, selective-execution, test-impact-analysis, cost, measurement]
related:
  [
    /plans/active/issues/test_impact_selective_execution_design_2026_08_03.md,
    /plans/active/issues/quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
source:
  "Interactive session: after publishing the selective-test-execution design doc, the operator asked for a rough
  minutes-saved estimate; a 4-repo commit sample was run live to ground it instead of guessing. Operator then asked to
  extend that sample to the full fleet and track it as a human plan, to be dispatched (assigned_vm flipped to planning)
  after a session /pre-compact checkpoint."
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Test-impact / selective execution — fleet-wide eligibility measurement, then staged rollout

## Why this plan exists

`test_impact_selective_execution_design_2026_08_03.md` designed a conservative, escape-hatch-heavy selector for running
only the pytest files a diff can plausibly affect. Its own follow-up gates all implementation on an operator review.
Before that review, the operator asked how many minutes this would actually save — the honest answer needed real data,
not an industry-average guess, because this codebase's dynamic-dispatch adapter/family patterns (found live in
`execution-service` and `features-service`) are exactly the kind of thing that defeats a naive estimate.

**A live 4-repo sample (last 50 commits / 30 days each, classified against the design's actual escape-hatch rules)
already found real, repo-specific variance**:

| Repo                             | `.py`-touching commits sampled | Hit the dynamic-dispatch escape hatch | Narrow-eligible |
| -------------------------------- | ------------------------------ | ------------------------------------- | --------------- |
| `execution-service`              | 17                             | 11 (65%)                              | **35%**         |
| `features-service`               | 35                             | 2 (6%)                                | **94%**         |
| `instruments-service`            | 36                             | 5 (14%)                               | **86%**         |
| `market-data-processing-service` | 26                             | 1 (4%)                                | **96%**         |

Blended against a ~9 min baseline `QG slice (tests)` leg (measured earlier on `features-service`) and an assumed 20-40%
narrowed-runtime reduction (industry-typical, NOT measured here), this gave a rough **~4-6 min/run saved on the three
high-eligibility repos, ~2-3 min/run on `execution-service`** — directionally useful, but only 4 of ~23 Python repos
were sampled, and the dynamic-dispatch classifier was a rough regex proxy, not a verified allowlist. This plan closes
both gaps before anyone trusts the number for a real rollout decision.

## Phase 1 — Fleet-wide measurement (unblocked, start immediately)

- [ ] [SCRIPT] P1. **Extend the commit-classification sample to every remaining Python fleet repo.** Repos already
      sampled: `execution-service`, `features-service`, `instruments-service`, `market-data-processing-service`.
      Remaining, per `workspace-manifest.json`'s 25-repo list, excluding the 2 non-Python UI repos
      (`unified-trading-system-ui`, `deployment-ui` — out of scope by construction, the design is pytest-specific):
      `agent-orchestrator`, `alerting-service`, `batch-live-reconciliation-service`, `client-reporting-api`,
      `deployment-api`, `deployment-service`, `e2e-testing`, `fund-administration-service`, `greeks-service`,
      `ibkr-gateway-infra`, `ml-service`, `strategy-service`, `system-integration-tests`, `trading-agent-service`,
      `unified-api-contracts`, `unified-trading-api`, `unified-trading-library`, `unified-trading-pm` (18 repos). Same
      methodology as the 4-repo sample above: last 50 commits / 30 days per repo, classify each `.py`-touching commit as
      narrow-eligible or escape-hatch-hit (conftest.py touch, manifest/config touch, suspected
      dynamic-dispatch-directory touch). Done-when: a per-repo table (repo, commits sampled, `.py`-touching count,
      escape-hatch-hit rate, narrow-eligible %) exists for all 22 Python repos (4 already done + 18 here), committed
      into this plan's Progress Log or a linked results doc — not left in a scratchpad (see the dangling-reference
      lesson in `quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md`).
- [ ] [SCRIPT] P1. **Turn the full 22-repo table into a real fleet-wide minutes-saved estimate**, distinguishing local
      `quality-gates.sh` runtime from self-hosted CI wall-clock (same pytest leg, same eligibility numbers, different
      audience — CI runs less often per-engineer than local QG does, so state both a per-run figure and, where real
      per-repo commit-frequency data is available, a rough daily/weekly aggregate). Explicitly label every number as
      either MEASURED (the escape-hatch-hit rate, which is real) or ASSUMED (the 20-40% narrowed-runtime-reduction
      figure, which is an industry-typical guess, not measured in this codebase). Done- when: the estimate is written up
      with its derivation shown (repo × frequency × eligibility × assumed- reduction), not just a final number.
- [ ] [SCRIPT] P2. **Replace the regex dynamic-dispatch heuristic with a real, verified allowlist.** The 4-repo sample
      used a rough proxy (`trade_execution/`, `/adapters?/`, `_adapter.py$`, `api/main.py$`) that over- matches (e.g.
      any directory literally named `adapter` regardless of whether it actually does
      `importlib.import_module`/`__getattr__`/`__import__` dispatch). For every repo flagged with a non-trivial
      dynamic-dispatch hit rate in Phase 1, read the actual flagged files and confirm genuine dynamic-dispatch usage
      (file:line citing the real call), building the hand-curated allowlist the design's escape-hatch table already
      calls for. Done-when: a per-repo allowlist exists where every entry cites a verified file:line, and the Phase-1
      eligibility table is re-run against the verified allowlist (not the regex proxy) to confirm whether the numbers
      move.

## Phase 2 — Implementation (BLOCKED-OPERATOR-DECISION — do not start)

> Every todo below is gated on the "Operator review of this design" todo already tracked in
> `test_impact_selective_execution_design_2026_08_03.md` (not duplicated here as a checkbox — that doc's own checkbox is
> the real one). None of these are dispatchable, regardless of this plan's `assigned_vm`, until that review closes and
> explicitly authorizes implementation. Scoped here now so the roadmap is complete and each stage is independently
> checkable once unblocked — not so any of it starts early.

- [ ] [INFRA] P1. BLOCKED-OPERATOR-DECISION: **Build the workspace-wide import-graph walker**, extending
      `check_removed_symbols.py`'s existing `ast.walk()`-over-`Import`/`ImportFrom` pattern into a
      `file → {imported files}` edge table, inverted to `file → {transitive importers}`, cached via the same
      content-sentinel key pattern `content-gate` already uses. Done-when: the walker runs against a real repo and
      produces a verifiably-correct edge table for a hand-checked sample of files (cross-referenced against
      `grep -rn "^import\|^from"` for the same files).
- [ ] [INFRA] P1. BLOCKED-OPERATOR-DECISION: **Wire the Phase-1 verified allowlists (dynamic-dispatch, conftest tree,
      config/data artifacts) into the walker as escape-hatch checks**, producing the binary
      `RUN_FULL_SUITE=true`/narrowed-set output the design's fallback rule specifies. Done-when: given a synthetic diff
      touching each escape-hatch category, the walker emits `RUN_FULL_SUITE=true`; given a synthetic self-contained
      diff, it emits a correctly-narrowed set.
- [ ] [REVIEW] P1. BLOCKED-OPERATOR-DECISION: **Build the golden-set selector regression tests** (design doc layer 1) —
      a fixture repo/frozen snapshot with known import relationships, a known dynamic-dispatch file, a known multi-level
      `conftest.py` tree, and a known config-driven test, asserting the selector's exact expected output for every safe
      case and every escape-hatch category. Done-when: this suite is wired into the SAME repo's own `quality-gates.sh`
      so a regression in the selector itself is caught the same way any other code regression is.
- [ ] [REVIEW] P1. BLOCKED-OPERATOR-DECISION: **Single-repo shadow-mode trial**, on the highest-eligibility repo from
      the Phase-1 measurement (candidates per the 4-repo sample: `market-data-processing-service` or `features-service`,
      ~94-96% eligible) — run the selector in parallel with the real full suite for 2 weeks, always actually executing
      the full suite, logging any divergence. Done-when: zero observed divergences over the full 2-week window; a single
      divergence resets the trial and is filed as its own issue doc (a design bug, not noise).
- [ ] [REVIEW] P2. BLOCKED-OPERATOR-DECISION: **Fleet-wide shadow-mode trial**, only after the single-repo trial passes
      clean — same methodology, 2 weeks, across every repo from the Phase-1 table with the current allowlists.
      Done-when: zero observed divergences fleet-wide over the full window.
- [ ] [REVIEW] P2. BLOCKED-OPERATOR-DECISION: **Promotion decision** — once the fleet shadow trial is clean, decide
      whether to let the selector actually skip real test execution (vs. keep it shadow-only indefinitely), plus stand
      up the post-promotion nightly full-suite canary the design specifies. This is itself an operator call, not a
      worker todo — state the shadow-trial evidence and ask.

## Progress Log

- **2026-08-03**: Plan authored as a LOCAL/human plan (`assigned_vm: NA`) per operator instruction — Phase 1 is ready to
  dispatch (flip to `assigned_vm: planning`) once the operator does so after their own `/pre-compact` checkpoint; Phase
  2 stays non-dispatchable regardless via its `BLOCKED-OPERATOR-DECISION` tags until the design review closes.
