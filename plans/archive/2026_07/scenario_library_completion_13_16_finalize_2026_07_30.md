---
doc_type: plan
title: Finalize — scenario library completion (execution_slippage_spike + lst_unstake_queue_blowup)
summary:
  Gated close-out twin for scenario_library_completion_13_16_2026_07_27, reclassified NA -> planning by
  /na-eligibility-audit defi on 2026-07-30. Reconciles the source plan's checkboxes, confirms both ScenarioOverlay
  entries are genuinely consumed downstream, and checks archival eligibility once the source plan's todos are done.
status: complete # (was: active) 2026-07-31 — all 3 todos [x], source plan archived alongside this doc
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [ao-dispatch, close-out, reclassification, na-audit, scenario-injection]
related:
  [
    /plans/archive/2026_07/scenario_library_completion_13_16_2026_07_27.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: backend_engineer
drift_direction: none
locked_by:
locked_since:
supersedes: []
superseded_by:
depends_on: [scenario_library_completion_13_16_2026_07_27]
gate_on_depends: true
source:
  [
    "/na-eligibility-audit defi, 2026-07-30 — paired finalize twin authored per
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 1(b) (retroactive reclassification:
    assigned_vm flipped in place, name unchanged, bolt-on finalize sibling dated the day of the pass).",
  ]
---

# Finalize — scenario library completion (13 + 16)

> **ARCHIVED (2026-07-31) — all 3 todos shipped, source plan archived alongside this doc.**

> **Gated twin.** `depends_on` + `gate_on_depends: true` held every todo here until every todo in
> `/plans/archive/2026_07/scenario_library_completion_13_16_2026_07_27.md` was done — satisfied 2026-07-31.

## Todos

- [x] ✅ [VALIDATE] P3. **DONE 2026-07-31.** Confirmed both entries are genuinely consumed, not just registered — cited
      consumer: `unified-trading-library`'s `ScenarioOverlayApplier.apply()`
      (`unified_trading_library/scenario/applier.py`), which discriminates generically on `mutation_type` and already
      dispatches `BookSpoof` (`execution_slippage_spike`) and `LatencyInject` (`defi_lst_unstake_queue_blowup`) — no
      applier code change was needed. Concrete proof:
      `tests/unit/scenario/test_applier.py::     test_every_registry_scenario_applies_without_error`, parametrized over
      the FULL `SCENARIO_REGISTRY`, ran green for both new scenario_ids (13/13 registry entries pass) with zero
      test-file edits required — the smoke test already picks up any new registry entry automatically.
- [x] ✅ [DOC] P3. **DONE 2026-07-31.** Every todo in `scenario_library_completion_13_16_2026_07_27.md` is `- [x]` with
      `unified-api-contracts@15ab5a48` cited. Both `scratch_scenarios_day1/13_execution_slippage_spike.md` and
      `16_lst_unstake_queue_blowup.md` updated with a `🟢 SHIPPED` banner naming the registry entry each now backs
      (`unified-trading-pm@df6703be9`).
- [x] ✅ [PM] P3. **DONE 2026-07-31.** Source plan: every todo done, `locked_by:` empty — archival-eligible. Ran the
      6-step ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): (1) no deferred items to
      migrate (all 3 todos genuinely complete, nothing left prose-only); (2) archived-banner + `superseded_by: none`
      (terminal — the scenario is now registry-resident, not superseded by another plan); (3) codex-alignment check — no
      new contract established (routine registry addition following the pre-existing `DEFI_CHAIN_RPC_OUTAGE_SOLANA`
      pattern, nothing to stub); (4) no new CLAUDE.md rule needed for the same reason; (5) corpus-wide referrer sweep —
      fixed `plans/active/INDEX.md`; `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s mention is historical Progress
      Log prose from a past audit dated before this completion, left as-is (not a live path reference); the 2026-07-24
      archive-dashboard snapshot is itself already an archived point-in-time doc, not edited retroactively; (6) both
      this finalize doc and the source plan move to `plans/archive/2026_07/` via a clean `git mv` in the NEXT commit
      (deliberately split from this content-edit commit, per the checkbox-flip-then-archive-move discipline — never
      combine an edit with the `git mv` in one commit, see `unified-trading-pm/agents/RULES.md` § 2).

## Progress Log

- **2026-07-30** — Authored by `/na-eligibility-audit defi` as the paired finalize twin for a `NA -> planning`
  reclassification. The source plan cleared the shared conflict-check (§ 3 of the naming/conflict-check SSOT) against
  all 231 currently-active `assigned_vm: planning` docs: zero open todo anywhere in the corpus duplicates its claim.
