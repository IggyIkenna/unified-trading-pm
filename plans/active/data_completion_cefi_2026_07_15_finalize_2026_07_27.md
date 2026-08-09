---
doc_type: plan
title: >-
  data_completion_cefi_2026_07_15 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for data_completion_cefi_2026_07_15.md -- machine-held via depends_on + gate_on_depends: true until all
  of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once its AO-dispatched todos ship
  (citing each landing commit), then archives it via the standard 6-step ritual once fully closed. Authored 2026-07-27
  as part of na_docs_validity_and_ao_eligibility_audit_2026_07_26.md's Phase 1 reclassification pass, per
  task_template.md's finalize-plan-coverage rule (every assigned_vm:planning plan needs a companion gated finalize
  plan).
status: active
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/data_completion_cefi_2026_07_15.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-30"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [data_completion_cefi_2026_07_15]
gate_on_depends: true
source: >-
  na_docs_validity_and_ao_eligibility_audit_2026_07_26.md Phase 1 (2026-07-27) -- data_completion_cefi_2026_07_15.md was
  reclassified assigned_vm:NA -> planning after verifying its remaining open todos are bounded/deterministic and
  conflict-free against currently-active AO plans; this finalize doc closes the finalize-plan-coverage gate the
  reclassification itself triggered.
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/active/data_completion_cefi_2026_07_15.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# data_completion_cefi_2026_07_15 — finalize

> **STATUS: `active` (matches frontmatter) — MACHINE-GATED, not yet dispatchable.** `gate_on_depends: true` already
> holds this plan's tasks until `data_completion_cefi_2026_07_15`'s todos are all done — a `status: draft` double-gate
> on top is redundant and, per `check_finalize_plan_coverage.py`'s ratchet (2026-07-30 corpus-wide fix), actively wrong:
> it stops nothing dispatch already prevents and requires a manual flip nothing automates. **Corrected 2026-08-09
> (plan_reconciler agt-5f7f31)** — this banner previously said `draft`, contradicting the frontmatter's `status: active`
> above; the frontmatter was the QG-correct side.

## Todos

- [ ] [REVIEW] P2. **Reconcile `data_completion_cefi_2026_07_15.md`'s checkboxes** against whatever shipped -- flip each
      `- [ ]` to `- [x]` citing the landing commit(s), confirm no residual work was missed, then run the standard 6-step
      archival ritual (migrate DEFERRED items, banner, codex-alignment check, update any CLAUDE.md/codex pointer on a
      new contract, update every referrer's path corpus-wide, clear lock) if the plan is fully closed. If real work
      remains after the AO-dispatched todos land, leave `data_completion_cefi_2026_07_15.md` active (do not
      force-archive) and note what's still open here instead.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (4 entries) -- finalize gate doc, code-free
  by rule; gated source doc + the reclassification audit that spawned this gate + the archival-discipline codex + the
  skill remain the minimal correct set.
