---
doc_type: plan
title: >-
  canonical_id_builder_retrofit_checklist_2026_07_08 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for canonical_id_builder_retrofit_checklist_2026_07_08.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched todos ship (citing each landing commit), then archives it via the standard 6-step ritual once fully
  closed. Authored 2026-07-27 as part of na_docs_validity_and_ao_eligibility_audit_2026_07_26.md's Phase 1
  reclassification pass, per task_template.md's finalize-plan-coverage rule (every assigned_vm:planning plan needs a
  companion gated finalize plan).
status: draft
nature: process
asset_group: [cefi, defi, prediction, sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: instruments_master
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
depends_on: [canonical_id_builder_retrofit_checklist_2026_07_08]
gate_on_depends: true
source: >-
  na_docs_validity_and_ao_eligibility_audit_2026_07_26.md Phase 1 (2026-07-27) --
  canonical_id_builder_retrofit_checklist_2026_07_08.md was reclassified assigned_vm:NA -> planning after verifying its
  remaining open todos are bounded/deterministic and conflict-free against currently-active AO plans; this finalize doc
  closes the finalize-plan-coverage gate the reclassification itself triggered.
assigned_role: data_engineering
drift_direction: advance-code
---

# canonical_id_builder_retrofit_checklist_2026_07_08 — finalize

> **STATUS: `draft` — NOT dispatched.** Flips to `active` only once the gated plan's todos are done (or on explicit
> operator direction to start reconciling early). Machine-gated via `depends_on` + `gate_on_depends: true`.

## Todos

- [ ] [REVIEW] P2. **Reconcile `canonical_id_builder_retrofit_checklist_2026_07_08.md`'s checkboxes** against whatever
      shipped -- flip each `- [ ]` to `- [x]` citing the landing commit(s), confirm no residual work was missed, then
      run the standard 6-step archival ritual (migrate DEFERRED items, banner, codex-alignment check, update any
      CLAUDE.md/codex pointer on a new contract, update every referrer's path corpus-wide, clear lock) if the plan is
      fully closed. If real work remains after the AO-dispatched todos land, leave
      `canonical_id_builder_retrofit_checklist_2026_07_08.md` active (do not force-archive) and note what's still open
      here instead.
