---
doc_type: plan
title: UI satellite AO batch 5 — finalize (reconcile source-doc citation + archive)
summary: >-
  Gated closeout for `ui_satellite_ao_dispatch_batch5_2026_08_21.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until its 1 todo is done. Upgrades `artifact_pipeline_observability_2026_07_17.md`'s
  already-flipped extraction-pointer checkbox to real shipped evidence, then archives the batch doc via the standard
  6-step ritual.
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ui, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/ui_satellite_ao_dispatch_batch5_2026_08_21.md,
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ui_satellite_ao_dispatch_batch5_2026_08_21]
gate_on_depends: true
source: >-
  na-eligibility-audit 2026-08-21 RECLASSIFY-per-todo-split extraction, per `task_template.md` §4's
  finalize-plan-coverage rule.
assigned_role: infra
effort: low
sequential: true
drift_direction: advance-docs
context_scope:
  [
    /plans/active/ui_satellite_ao_dispatch_batch5_2026_08_21.md,
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
  ]
---

# UI satellite AO batch 5 — finalize

> **Machine-gated on `ui_satellite_ao_dispatch_batch5_2026_08_21.md`** (`depends_on` + `gate_on_depends: true`).
> `sequential: true` because the source-doc citation upgrade (todo 1) should land before archival (todo 2).

## Todos

- [ ] [REVIEW] P3. **Reconcile evidence into the true source doc.** Verify the batch's `<repo>@<sha>` evidence is a
      real commit ancestor of `origin/live-defi-rollout`, then upgrade
      `artifact_pipeline_observability_2026_07_17.md`'s Phase 1 Snapshot-worker checkbox from the bare
      extraction-pointer to the real shipped evidence (`<repo>@<sha>` + the quality-gates/test citation). Also
      re-check whether that source doc's remaining 3 items (What's running tab / SHA-pinning stretch /
      misattributed-VM-origin correction) have changed state since 2026-08-21 and need a fresh note.
- [ ] [DOC] P3. **Archive this batch doc** — once todo 1 lands, run the standard 6-step archival ritual on
      `ui_satellite_ao_dispatch_batch5_2026_08_21.md` (move to `plans/archive/2026_08/`, exact-successor banner, fix
      every corpus referrer). Distinct `[DOC]` tag from todo 1's `[REVIEW]` tag per `task_template.md`'s same-tag-
      same-priority `/done`-collision finding (2026-07-31).

## Progress Log

- **2026-08-21**: Authored alongside batch5 (na-eligibility-audit, ui tranche, RECLASSIFY-per-todo-split of
  `artifact_pipeline_observability_2026_07_17.md`).
