---
doc_type: plan
title: Fund Administration Redemption/NAV Cadence Engine — Finalize
summary:
  Gated finalize plan for fund_administration_redemption_cadence_engine_2026_08_20 — reconciles evidence, re-checks
  any deferred follow-up (real NAV-source location, treasury-ledger consumer wiring), and runs the 6-step archival
  ritual once every todo in the source plan is done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [fund-administration-service, unified-api-contracts]
scope: [engineer]
tags: [fund-administration, redemption, finalize, archival]
related:
  [
    /plans/active/fund_administration_redemption_cadence_engine_2026_08_20.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: [fund_administration_redemption_cadence_engine_2026_08_20]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: companion finalize plan per task_template.md §4 STRICT rule, 2026-08-20
context_scope:
  [
    /plans/active/fund_administration_redemption_cadence_engine_2026_08_20.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Fund Administration Redemption/NAV Cadence Engine — Finalize

**Why this doc exists**: `task_template.md`'s STRICT rule requires a gated finalize companion for every
`assigned_vm: planning` plan — this reconciles the source plan's evidence, re-checks anything deferred at authoring
time, and runs the archival ritual so the source plan doesn't sit `active` with zero open todos.

## Todos

- [ ] [REVIEW] P1. Reconcile every completed todo in `fund_administration_redemption_cadence_engine_2026_08_20.md`
  against its cited evidence (commit SHA, test name, QG run) — re-verify each cited commit actually exists and
  actually contains the claimed change, not just that the checkbox is flipped. Done-when: every `[x]` todo's evidence
  is independently re-confirmed, or a discrepancy is logged and routed back to a new todo.

- [ ] [REVIEW] P1. Re-check the two config-default decisions left open at authoring time (`redemption_cadence_seconds`
  default 8h, `redemption_fee_pct` default 0) — confirm whether the operator has since set a production value for
  either; if so, verify the shipped default matches. If still unset, leave as-is (a config default, not a blocker) and
  note it in the Progress Log below rather than escalating.

- [ ] [DOC] P2. Run the 6-step archival ritual on
  `fund_administration_redemption_cadence_engine_2026_08_20.md` once every one of its todos is `[x]` and unlocked:
  dated archive folder move, exact-successor banner, corpus-wide referrer-path fixup. Done-when: `git mv` lands the
  source plan into `plans/archive/2026_08/` and `run_hygiene_sweep.sh` shows zero broken referrers to its old path.

## Progress Log

- **2026-08-20**: Finalize plan authored alongside its source plan per the STRICT companion-finalize-plan rule.
