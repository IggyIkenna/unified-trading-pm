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

- [ ] [REVIEW] P1. Re-verify each of `recursive_loop_orchestrator_wiring_2026_08_09.md`'s 8 todos: confirm the cited
      commit(s) actually exist and the cited test(s) actually pass green (re-run, don't trust the recorded evidence line
      alone). Reconcile the evidence into
      `plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`'s `[DESIGN]`
      `RecursiveLoopOrchestrator` translation-layer todo — flip it `[x]` done, citing every repo@sha this plan produced.
      Repo: unified-trading-pm. Done-when: the source doc's todo is flipped with a full evidence trail, and re-running
      each cited test independently still passes.
- [ ] [REVIEW] P2. Re-check the Family-2 hedge-poller audit todo's outcome (recursive_loop_orchestrator_wiring's 6th
      todo): if it found no suitable poller existed and filed a follow-up `[DESIGN]` todo, confirm that follow-up was
      actually filed (not just mentioned in prose) as a real `- [ ]` item somewhere trackable — file it now if it was
      described but never actually written as a checkbox. Repo: unified-trading-pm. Done-when: the follow-up either
      doesn't apply (a poller was found and wired) or exists as a real tracked `- [ ]` todo.
- [ ] [DOC] P1. Run the standard 6-step archival ritual on `recursive_loop_orchestrator_wiring_2026_08_09.md` once every
      one of its todos is `[x]` and unlocked: move it to `plans/archive/2026_08/`, fix every corpus referrer path
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), and confirm `run_hygiene_sweep.sh` stays
      green. Repo: unified-trading-pm. Done-when: the file is under `plans/archive/2026_08/`, `status: complete`, 0
      broken referrer links, hygiene sweep green.

## Progress Log

- **2026-08-09**: authored alongside the parent plan as `status: active` — held purely via
  `depends_on: [recursive_loop_orchestrator_wiring_2026_08_09]` + `gate_on_depends: true` (dispatch stays
  machine-blocked until the parent's todos complete), not the draft-gated phase-chain pattern — the hygiene gate flagged
  `status: draft` here as redundant once `gate_on_depends` already holds it (`task_template.md` §4).
