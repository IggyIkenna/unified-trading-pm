---
doc_type: plan
title: Finalize — RecursiveLoopOrchestrator wiring plan reconciliation + archival
summary: >-
  Gated finalize companion to recursive_loop_orchestrator_wiring_2026_08_09.md. Reconciles every completed todo's
  evidence back into the source issue doc's [DESIGN] todo, re-checks the Family-2 hedge-poller audit's deferred outcome,
  and runs the 6-step archival ritual on the now-complete parent plan.
status: active
nature: process
asset_group: [defi]
stage: [strategy]
repos: [strategy-service, execution-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [defi, carry, recursive-loop, finalize, archival]
related:
  [
    /plans/active/recursive_loop_orchestrator_wiring_2026_08_09.md,
    /plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: [recursive_loop_orchestrator_wiring_2026_08_09]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  Companion finalize plan, authored alongside recursive_loop_orchestrator_wiring_2026_08_09.md per the workspace's
  mandatory finalize-plan-for-every-AO-plan rule.
context_scope:
  [
    /plans/active/recursive_loop_orchestrator_wiring_2026_08_09.md,
    /plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md,
  ]
---

# Finalize — RecursiveLoopOrchestrator wiring

## Todos

- [x] ✅ [REVIEW] P1. Re-verify each of `recursive_loop_orchestrator_wiring_2026_08_09.md`'s 8 todos: confirm the cited
      commit(s) actually exist and the cited test(s) actually pass green (re-run, don't trust the recorded evidence line
      alone). Reconcile the evidence into
      `plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`'s `[DESIGN]`
      `RecursiveLoopOrchestrator` translation-layer todo — flip it `[x]` done, citing every repo@sha this plan produced.
      Repo: unified-trading-pm. Done-when: the source doc's todo is flipped with a full evidence trail, and re-running
      each cited test independently still passes.
- [x] ✅ [REVIEW] P2. Re-check the Family-2 hedge-poller audit todo's outcome (recursive_loop_orchestrator_wiring's 6th
      todo): if it found no suitable poller existed and filed a follow-up `[DESIGN]` todo, confirm that follow-up was
      actually filed (not just mentioned in prose) as a real `- [ ]` item somewhere trackable — file it now if it was
      described but never actually written as a checkbox. Repo: unified-trading-pm. Done-when: the follow-up either
      doesn't apply (a poller was found and wired) or exists as a real tracked `- [ ]` todo. — unified-trading-pm.
      Independently re-verified 2026-08-09 (slot 29, review): the parent plan's todo 6 outcome is
      `(b) no suitable     poller exists` (confirmed via the parent plan's own Progress Log + Todos section —
      `HealthFactorMonitor` has zero production callers, no Cloud-Scheduler endpoint exists); the required follow-up
      `[DESIGN]` todo IS a real trackable `- [ ]` checkbox in this same file (todo 4 below, "Decide + scope the RIGHT
      mechanism..."), not prose-only — confirmed via direct grep of the live file content, not a trust of the prior
      session's claim.
- [ ] [DOC] P1. Run the standard 6-step archival ritual on `recursive_loop_orchestrator_wiring_2026_08_09.md` once every
      one of its todos is `[x]` and unlocked: move it to `plans/archive/2026_08/`, fix every corpus referrer path
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), and confirm `run_hygiene_sweep.sh` stays
      green. Repo: unified-trading-pm. Done-when: the file is under `plans/archive/2026_08/`, `status: complete`, 0
      broken referrer links, hygiene sweep green.
- [ ] [DESIGN] P2. Decide + scope the RIGHT mechanism to make `PerpHedgeSizer.compute_rebalance()`/
      `.compute_margin_topup()` (Family-2 `CARRY_BASIS_PERP_INV`) live-reachable on its documented 5-min poll cadence
      (`perp_hedge_sizer.py:60-63`). The parent plan's todo 7 audit (2026-08-09, slot 8) confirmed execution-service has
      **no suitable existing poller**: `HealthFactorMonitor` (`defi_execution/monitors/health_factor_monitor.py`) is a
      real asyncio poll-loop primitive but itself has zero production callers (not started in `api/app.py`'s
      `@app.on_event("startup")` or `cli/main.py`); `start_domain_config_reloaders()` (the one live-reachable
      scheduling-adjacent mechanism, `api/app.py:149-152`) wraps UTL's pub/sub event-driven `DomainConfigReloader` —
      wrong shape for a fixed-cadence business-logic tick; no Cloud-Scheduler-triggered HTTP endpoint exists anywhere in
      the service. Candidate shapes to weigh (operator/main judgment call, not a worker's to freehand): (1) a new
      `HealthFactorMonitor`-pattern in-process asyncio poll loop wired at `api/app.py` startup, one instance per open
      Family-2 position; (2) a Cloud-Scheduler-triggered admin HTTP endpoint (5-min cron hitting execution-service,
      mirroring how other periodic jobs in the workspace are wired — see
      `/codex/05-infrastructure/vm-launcher-runbook.md`-adjacent scheduled-job patterns); (3) piggybacking on
      strategy-service's existing `V2EngineOrchestrator.on_tick()` cadence via the same `leg_controller_runner.py`
      bridge `recursive_loop_runner.py` already uses, rather than adding a second independent scheduler to
      execution-service. Repo: execution-service (+ possibly infra, if Cloud Scheduler is the ruled shape). Done-when:
      the operator/main rules on the mechanism, and a properly-scoped implementation todo (with exact done-when + test
      plan) is filed against that ruling.

## Progress Log

- **2026-08-09**: authored alongside the parent plan as `status: active` — held purely via
  `depends_on: [recursive_loop_orchestrator_wiring_2026_08_09]` + `gate_on_depends: true` (dispatch stays
  machine-blocked until the parent's todos complete), not the draft-gated phase-chain pattern — the hygiene gate flagged
  `status: draft` here as redundant once `gate_on_depends` already holds it (`task_template.md` §4).
- **2026-08-09 (slot 8, backend_engineer)**: Added the `[DESIGN]` follow-up todo above per the parent plan's todo 7
  audit outcome (no suitable existing poller for `PerpHedgeSizer` — full grep evidence in the parent plan's Progress
  Log). This satisfies todo 2 above's "confirm the follow-up was actually filed as a real `- [ ]` item" check in advance
  — filed now rather than left as prose.
- **2026-08-09 (slot 25, review)**: Todo 1 shipped — independently re-verified all 8 of the parent plan's todos.
  Confirmed all 6 distinct cited commits exist AND are ancestors of `origin/live-defi-rollout`
  (`unified-api-contracts@547b1d1b`, `strategy-service@b98f74fb`/`817bb4e0`/`f2ac7fdf`/`d6c86f44`,
  `execution-service@2352a17e`). Re-ran full `quality-gates.sh --no-fix` (not just the cited unit tests — the full
  suite, per RULES.md's "never run pytest directly") on all 3 touched repos, all green: unified-api-contracts (396s,
  includes `resolve_ltv_mode` 0.93/0.945/0.86 assertions), strategy-service (5836 passed, 199s, includes the
  `n_loops`/`ltv_per_loop` catalog tests + both Family-1/2 `on_tick()` test files), execution-service (7895 passed,
  226s, includes `test_recursive_loop_runner.py`). Confirmed both archetypes are genuinely absent from
  `_ALLOWED_EMPTY_ARCHETYPES` (todo 8) via direct dict-content inspection, not just a checkbox read. Re-ran todo 7's
  audit greps verbatim — findings match exactly (no suitable poller exists; `HealthFactorMonitor` has zero production
  callers; no Cloud-Scheduler endpoint). Flipped the source issue doc's `[DESIGN]` `RecursiveLoopOrchestrator`
  translation-layer todo (`defi_catalog_engine_config_key_contract_drift_2026_07_23.md`) to `[x]` with the full evidence
  trail. Found + recorded (non-blocking) two minor evidence-line inaccuracies in the parent plan's Progress Log: the
  Family-1 `on_tick()` test file has 5 tests not the claimed 6; `test_recursive_loop_runner.py` has 11 tests not the
  claimed 13 — both files are correct and complete, only the narrated counts were off; not worth a follow-up todo.
- **2026-08-09 (slot 29, review)**: Todo 2 shipped — independently re-checked the parent plan's todo 6 (Family-2
  hedge-poller audit) outcome and confirmed the required follow-up `[DESIGN]` todo (todo 4 in this file) is a genuine
  tracked `- [ ]` checkbox, not prose-only. No new todo needed — slot 8 already filed it correctly on 2026-08-09.
