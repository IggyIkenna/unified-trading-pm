---
doc_type: plan
title: BYBIT-SPOT manifest remediation — finalize (reconcile source docs + archive)
summary: >-
  Gated closeout for `cefi_bybit_spot_manifest_remediation_2026_07_25.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 5 of that plan's todos are done. Authored per `task_template.md`'s "Every
  AO-dispatched plan needs a gated finalize plan" rule (operator ruling 2026-07-24), which the parent plan shipped
  without (`check_finalize_plan_coverage.py` regression, corrected here — the parent's own todo 5 already scopes most
  of the reconciliation work; this finalize plan's real remaining job is the archival ritual once that lands).
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, bybit-spot, manifest-surgery, close-out, archival]
related:
  [
    /plans/active/cefi_bybit_spot_manifest_remediation_2026_07_25.md,
    /plans/active/cefi_misc_audits_and_hygiene_2026_07_25.md,
    /plans/archive/issues/bybit_spot_manifest_stray_captures_2026_07_07.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_bybit_spot_manifest_remediation_2026_07_25]
gate_on_depends: true
source: >-
  Authored to close a `check_finalize_plan_coverage.py` ratchet regression (a new `assigned_vm: planning` plan,
  `cefi_bybit_spot_manifest_remediation_2026_07_25.md`, shipped without a companion gated finalize plan) found while
  shipping unrelated `/ag-closeout-audit tradfi` work through the same quickmerge gate, 2026-07-25.
sequential: true
drift_direction: advance-code
---

# BYBIT-SPOT manifest remediation — finalize

> **Machine-gated on `cefi_bybit_spot_manifest_remediation_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 5 tasks in that plan are `done`.

## Todos

- [ ] [REVIEW] P2. **Verify the parent plan's own todo 5 ("Close the loop") actually reconciled both cited docs** —
      confirm `plans/active/cefi_misc_audits_and_hygiene_2026_07_25.md` carries a corrective note citing the parent
      plan's real shipped commit(s), and confirm `plans/archive/issues/bybit_spot_manifest_stray_captures_2026_07_07.md`
      either got its `status: resolved` re-confirmed TRUE with evidence, or received the banner correction noting the
      gap between "marked resolved" (2026-07-14) and "actually executed" (this plan's completion date). **Done when**:
      both cited docs are verified reconciled, or the reconciliation is completed here if the parent's todo 5 missed
      either piece.
- [ ] [DOC] P1. **Archive `cefi_bybit_spot_manifest_remediation_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm no remaining open work (all 5 parent todos done, todo above verified) →
      add the archive banner → run the codex-alignment check → grep the corpus for every referrer of
      `cefi_bybit_spot_manifest_remediation_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
