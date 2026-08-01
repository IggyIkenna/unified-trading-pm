---
doc_type: plan
title: Infra satellite AO batch 3 — finalize (reconcile source-doc checkboxes, do NOT archive either source)
summary: >-
  Gated closeout for infra_satellite_ao_dispatch_batch3_2026_07_30.md, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24; machine-enforced by
  scripts/quality_gates/check_finalize_plan_coverage.py, which is at baseline 0 — a 2-todo assigned_vm:planning plan
  without a gated twin is a hard regression, not a warning). Once both batch todos are done, reconciles the
  corresponding checkbox back into each source doc. Unusually for a finalize plan, the expected outcome is that NEITHER
  source doc becomes archivable — both were partial carve-outs and both keep judgment-gated todos at assigned_vm: NA —
  so this plan's main job is to flip accurately and then explicitly NOT archive, rather than to run the 6-step ritual on
  the sources. It does run the ritual on the batch pair itself.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, finalize, batch-3, plan-hygiene]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/active/issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md,
    /plans/active/issues/git_health_not_clean_since_pinned_constant_2026_07_27.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
sequential: true
drift_direction: advance-code
depends_on: [infra_satellite_ao_dispatch_batch3_2026_07_30]
gate_on_depends: true
locked_by:
locked_since:
context_scope:
  [
    /plans/active/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
supersedes:
superseded_by:
source: >-
  Authored alongside its parent batch by `/ag-closeout-audit infra` (2026-07-30), per the standing
  finalize-plan-coverage rule (every ≥2-todo assigned_vm:planning plan needs a gated finalize twin).
---

# Infra satellite AO batch 3 — finalize

> **⚠️ STATUS: `draft`** — flips to `active` with its parent; `gate_on_depends: true` additionally keeps the dispatcher
> from queueing this plan's todos until the parent's 2 todos are `[x]`.

## Todos

- [ ] [DOC] P2. **Reconcile both source docs' checkboxes — and deliberately do NOT archive either.** Once the parent
      batch's 2 todos are `[x]`: (1) in
      `issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md`, close the first
      `[SCRIPT] P2` item (the `--dry-run` gating fix) citing the parent todo's actual commit sha — **re-verify the sha
      exists** (`git show --stat <sha>`), do not trust the batch doc's own copy of the evidence line; (2) in
      `issues/git_health_not_clean_since_pinned_constant_2026_07_27.md`, close its first two `[BACKEND] P3` items (the
      two diagnostics) citing the recorded verdict, and if that verdict makes exactly one answer to todo 3 provably
      right, annotate todo 3 with the recommendation **without** closing it; (3) confirm each source doc still has
      genuine open todos and therefore stays `status: open`, `assigned_vm: NA` — expected residual is 2 items in the
      gitignore doc (template reconciliation + its gated `[VERIFY] P3`) and 1 in the git-health doc (the field-design
      fork). **If either doc unexpectedly reaches zero open todos, that is a real archival candidate** and gets the full
      6-step ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), not just a checkbox flip.
      **Done when**: each of the 4 extracted checkboxes is closed with a re-verified sha or explicitly left open with a
      re-confirmed reason, and each source doc's `status`/`assigned_vm` matches its actual residual.
- [ ] [DOC] P2. **Re-check the parent's Deferred table, then archive the batch pair.** (1) Re-test the two
      ruled-but-gated clusters the parent recorded as still-blocked — G1 (`base-service.sh`/`base-library.sh`
      serialization, entry #36) and G3 (`DataStatusTab.tsx` sequencing, entry #35): if
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s `base-service.sh` sub-item and
      `ci_satellite_ao_dispatch_batch2_2026_07_29.md`'s todos 1/11 have landed, and
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s `[INFRA] P2` part (B) has landed, those items are
      newly conflict-clear — **file them as a tracked follow-up todo/plan rather than executing them here** (this is a
      finalize plan, not an extraction vehicle). If still gated, record the re-measured state so the next reader does
      not re-derive it. (2) Re-test the parent's stop-iterating verdict: re-run
      `generate_ag_closeout_audit_candidates.py --tranche infra` and confirm the never-cited-orphan set is still purely
      non-batchable; if a new orphan with bounded work has appeared, say so explicitly (that is the one condition that
      would justify a batch4). (3) Run the standard 6-step archival ritual on the parent batch and on THIS plan. **Done
      when**: the Deferred re-check is recorded with measured evidence (not assumption), the stop-iterating verdict is
      either re-confirmed or explicitly retracted, and both plans of the pair are archived with every corpus-wide
      referrer path fixed.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
