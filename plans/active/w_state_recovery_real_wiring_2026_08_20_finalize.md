---
doc_type: plan
title: State recovery real wiring — finalize
summary: >-
  Gated finalize for w_state_recovery_real_wiring_2026_08_20 — independently re-verify recovery actually
  reconciles real state (not a stub dressed up as real), reconcile evidence back to the epic and T4 plan,
  archive once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution, state-recovery, order-recovery, finalize]
related:
  [
    /plans/active/w_state_recovery_real_wiring_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: [w_state_recovery_real_wiring_2026_08_20]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
sequential: true
source: Mandatory companion finalize per task_template.md's AO-plan rule (operator ruling 2026-07-24).
context_scope:
  [
    /plans/active/w_state_recovery_real_wiring_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
---

# State recovery real wiring — finalize

## Todos

- [x] ✅ [AGENT] P0. **Independently re-verify recovery reconciles REAL state, not stub-shaped state dressed up as
      real.** Don't trust the parent plan's own "done" claim: construct `OrderRecoveryEngine` with its real
      `OrderBook`/`_VenueAdapter` yourself, and confirm `fetch_open_orders()` genuinely calls a live/credentialed
      adapter method (not a hardcoded empty list still masquerading as "real"). This is the single highest-value
      check for this finalize — the whole point of the parent plan was closing exactly this gap.
      **Verified 2026-08-20** on a freshly-pulled `live-defi-rollout` tip (not the dispatch-time working copy):
      (1) `grep -n "class OrderBook\|class _VenueAdapter" -A 3 order_recovery.py` — zero "stub"/"minimal
      in-memory" language remains in either docstring; (2) `grep -rln "OrderRecoveryEngine(" execution_service/`
      excluding tests — still ZERO production instantiation sites, confirming Phase 3 todo 1 is genuinely,
      verifiably still unwired, not just claimed; (3) `bash scripts/quality-gates.sh --test --skip-lint` on the
      fresh pull — real exit code 0 (checked via `$?`, not `tee`'s), full suite including
      `test_venue_adapter_fetch_open_orders_calls_real_adapter_at_ccxt_boundary` (mocks only the ccxt exchange
      object's `.fetch_open_orders`, not `_VenueAdapter`/`BaseCLOBAdapter` methods themselves) passing.
- [x] ✅ [AGENT] P0. Reconcile every completed todo's evidence back to the epic's state-recovery section
      (`/plans/epics/system_readiness_master.md`) and to
      `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`'s own "Build state recovery" todo —
      both should point here as the real dispatch surface, not carry duplicate detail.
      **Done**: T4 plan's own todo already pointed here (shipped 2026-08-20) and now carries a terse
      "Final status" line with the 4 shipped shas + the `BLOCKED-OPERATOR` prerequisite pointer, not duplicate
      detail. Epic's bullet (`Execution carries full order lifecycle, state recovery, reconciliation and manual
      trade on every venue`) is a broader multi-part item — state recovery is only one clause of it — left
      correctly UNCHECKED rather than falsely marked done for a partial contribution; no epic edit was the
      correct call here, not an oversight.
- [x] ✅ [AGENT] P1. Check whether any `BLOCKED-CREDENTIALS` venues the parent plan filed are still genuinely
      blocked, or whether credentials have since become available — retag if resolved.
      **Checked 2026-08-20**: kraken (pending operator approval, `slot_11.md`), bitfinex, bitget (no live keys
      provisioned) — all three still genuinely `BLOCKED-CREDENTIALS`, no new information this session suggests
      otherwise. No retag needed.
- [ ] [AGENT] P1. **`BLOCKED-OPERATOR` — NOT closeable yet, genuine finding, not an oversight.** Run the
      archival ritual once every parent-plan todo is done and unlocked. **This todo's own premise doesn't hold
      today**: the parent plan (`w_state_recovery_real_wiring_2026_08_20`) has 2 genuinely open todos (Phase 3
      todo 1's startup-wiring, and the "run real recovery" Close-out todo), both explicitly `BLOCKED-OPERATOR`/
      `BLOCKED-CREDENTIALS`-tagged with dated reasons — but this task's OWN wording ("confirm zero open items
      (or explicit `BLOCKED-*` tags on the remainder)") turns out to be LOOSER than the authoritative codex SSOT
      it cites nowhere: `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` states unambiguously
      "A plan with every top-level todo `[x]` and no `locked_by` is DONE" — no `BLOCKED-*`-tag carve-out exists
      there. Per CLAUDE.md's own HARD RULE ("SSOT for a durable rule is a codex doc — never an active plan"), the
      codex doc's stricter rule governs, not this finalize plan's own looser phrasing. **Archival is correctly
      deferred, not performed**, until the parent's 2 open todos genuinely close (via
      `/plans/active/w_execution_orchestrator_oms_persistence_2026_08_20.md`'s own follow-up implementation plan
      landing, then Phase 3 todo 1 + the "run real recovery" todo re-attempted for real). Flagged to the
      coordinator 2026-08-20 rather than silently archiving against the stricter rule or silently leaving this
      todo's discrepancy unexplained.
