---
doc_type: plan
title: Cross-cutting satellite AO batch 3 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md — machine-held via depends_on +
  gate_on_depends: true until all 8 todos are done. Reconciles each named source doc's checkboxes independently, then
  re-checks batch 3's own Deferred items (2 operator-gated, 1 time-gated) for whether the gating ground has cleared, and
  archives the batch via the standard 6-step ritual.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-3, satellite-docs, archival]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
sequential: true
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cross_cutting_satellite_ao_dispatch_batch3_2026_08_01]
gate_on_depends: true
context_scope:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
source: >-
  /ag-closeout-audit cross-cutting re-invocation 2026-08-01, per task_template.md § 4's finalize-plan-coverage rule —
  every AO-dispatched plan needs a companion gated finalize plan.
---

# Cross-cutting satellite AO batch 3 — finalize

> **Machine-gated on
> [`cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md`](/plans/active/cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md)**
> (`depends_on` + `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 8 of that plan's
> todos are `done`. This plan itself ships `status: active` (not `draft`) per the 2026-07-30 no-double-gate finding —
> `gate_on_depends` alone already covers both an active AND a still-draft upstream batch, so a second `status: draft`
> rail here would just be a redundant manual flip nobody reliably remembers. `sequential: true` because todo 2 needs
> todo 1's reconciliation finished, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile every named source doc's checkboxes.** Batch 3's 8 todos cite 5 distinct source docs
      (each todo's text ends with `Source:`). For each: flip the corresponding checkbox, citing the batch commit that
      shipped it — verify the commit actually exists before citing it. After flipping, re-check each source doc for 0
      remaining open items (checkbox AND prose-form) and only then consider flipping its `status` to `resolved`.
      Specifically: `issues/feature_builder_registry_dag_dead_code_audit_2026_08_01.md` (3 of this batch's todos cite it
      — flip all 3 corresponding checkboxes, then check if the doc's own remaining scope — the `calendar`/`sports`
      engines the source doc itself notes as already checked or out of this audit's scope — is genuinely 0 open before
      flipping doc status), `issues/manifest_consolidator_cadence_cost_audit_2026_07_20.md`,
      `issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md` (2 todos cite it — both must flip before
      the doc has 0 open), `issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` (only follow-up 2 closes
      here — follow-up 1 stays open, operator-gated, so this doc stays `status: open`, do NOT flip it to resolved),
      `data_pipeline_alerts_batch_remediation_2026_07_15.md` (only its second open item closes here — its first item is
      time-gated, stays open, do NOT flip this doc to resolved either). **Done when**: every cited source checkbox is
      flipped with verified evidence and no doc's `status` was advanced past what its remaining items actually support.
- [ ] [REVIEW] P2. **Re-check batch 3's own Deferred items now that time has passed.** For the 2 operator-gated entries
      (`order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md`,
      `strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` follow-up 1) and the 1 time-gated entry
      (`data_pipeline_alerts_batch_remediation_2026_07_15.md`'s green-bookend observation): re-read the specific gating
      ground and decide whether it has cleared. Route each to exactly one of — ready for a batch 4 (note it), still
      genuinely gated (re-confirm with fresh evidence), or resolved independently. **Do NOT re-surface an operator
      question already asked** — if either operator-gated item is still unruled, leave it be rather than re-asking. Also
      verify the 6 `exclude_cross_cutting` mistags this batch found (see
      `issues/ag_closeout_audit_cross-cutting_parked_2026_08_01.md`) were actually picked up/retagged by their owning
      tranche's next audit pass — if any is still `asset_group: [cross-cutting]` and un-retagged after a reasonable
      interval, note that plainly rather than assuming it was handled. **Done when**: every Deferred entry and every
      parked mistag carries a dated re-verification verdict with its routing named.
- [ ] [DOC] P1. **Archive `cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md`** via the standard 6-step ritual:
      migrate any still-Deferred item to a tracked todo elsewhere (todo 2 above should have routed all 3) → add the
      archive banner → run the codex-alignment check (this batch introduces no new durable contract; confirm that is
      still true before archiving) → grep the corpus for every referrer of this batch or this finalize and fix each path
      → confirm `locked_by` is empty on both. **Done when**: both docs are in `plans/archive/2026_08/`, every corpus
      referrer resolves to the new path, and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard
      failures and 0 orphans.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.

## Progress Log

- **2026-08-01** — Drafted alongside batch3 (`/ag-closeout-audit cross-cutting`, autonomous, dispatch `agt-a5c7d6`, slot
  13). `status: active` from creation (no-double-gate finding); `gate_on_depends: true` holds every todo until batch3's
  8 todos are done.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries). NOTE: this doc's own "Codex SSOTs"
  section above cites `/codex/12-agent-workflow/ao-dispatch-batch-naming-and-conflict-check.md` and
  `/codex/11-project-management/plan-completion-and-archival-discipline.md` — both paths are STALE (the two docs' actual
  directories are swapped: the naming/conflict-check doc lives at `/codex/11-project-management/`, the
  archival-discipline doc at `/codex/12-agent-workflow/`). `context_scope` above uses the CORRECTED, disk-verified
  paths; the body line is left unedited per this pass's scope (frontmatter + Progress Log only) — flagging for a future
  doc-body fix.
- **plan_reconciler 2026-08-02** (whole-corpus pass, mechanical-adjudicator hunter): applied the doc-body fix flagged
  above — swapped the "## Codex SSOTs" section's two paths to their disk-verified locations (confirmed via `ls`):
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` and
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`. Now matches `context_scope`. See
  `/plans/active/issues/plan_reconciler_findings_undefined.md`.
