---
doc_type: plan
title: tradfi satellite AO batch 16 — finalize
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch16_2026_08_17.md — machine-held via depends_on +
  gate_on_depends until every todo in that batch is done. Reconciles each completed todo's evidence back into
  tradfi_reconciliation_2026_08_17_findings_2026_08_17.md's own checkboxes (this was an extraction batch, so the
  source doc's checkboxes — already flipped `[x]` with an EXTRACTED citation at drafting time — are the ones that
  need a real evidence line once the work actually lands), checks whether the source doc's one remaining NA item
  (multi-token symbol convention) has been resolved by an operator ruling in the interim, and runs the standard
  6-step archival ritual on the batch plan itself once closed.
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-batch, close-out, finalize, na-eligibility-audit]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch16_2026_08_17.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_satellite_ao_dispatch_batch16_2026_08_17]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch16_2026_08_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source:
---

# tradfi satellite AO batch 16 — finalize

> Machine-held (`depends_on` + `gate_on_depends: true`) until every todo in
> `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` is done.

## Todos

- [ ] [REVIEW] P1. **Reconcile each completed batch-16 todo's real evidence back into
      `tradfi_reconciliation_2026_08_17_findings_2026_08_17.md`.** The source doc's items 1/2/3/4/6/7/8/9 were
      already flipped `[x]` at drafting time with an `EXTRACTED → batch16 Todo N` citation (per this skill's
      standard convention) — that citation records the EXTRACTION, not completion. For each of batch-16's 8 todos,
      once actually done, update the corresponding source-doc item's citation to also carry the real completion
      evidence (commit sha / measured count / confirmed-state check) — do not trust a copied evidence line without
      re-verifying the cited commit/SHA/measurement actually exists.

- [ ] [REVIEW] P2. **Re-check whether the source doc's remaining NA item (item 5, multi-token equity symbol join
      convention — `BRK B` -> `BRK-B`/`BRK.B`) has had its gate clear since this batch was drafted** — specifically,
      whether an operator ruling on the naming convention has landed anywhere in the corpus in the interim. If so,
      spin the now-unblocked item into a fresh tracked todo (its own small batch, or folded into the next tradfi
      na-eligibility-audit pass) rather than leaving it silently stale.

- [ ] [REVIEW] P3. **Check whether reconciling `tradfi_reconciliation_2026_08_17_findings_2026_08_17.md`'s
      checkboxes (Todo 1 above) left it with 0 open items.** It will NOT reach zero as long as item 5 stays NA and
      unresolved (see Todo 2 above) — verify this explicitly rather than assume; if item 5 has since resolved AND
      all 8 extracted items are genuinely done, the source doc is now a full archival candidate and needs the
      standard 6-step ritual, not just its own checkbox flips.

- [ ] [DOC] P1. **Run the standard 6-step archival ritual on this batch plan itself**
      (`tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` + this finalize doc), including the corpus-wide
      referrer-path fixup, once all of the above is confirmed complete.

## Progress Log

- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-071b5c): drafted alongside the batch, gated on
  its completion per the AO-dispatched finalize-plan-coverage rule.
