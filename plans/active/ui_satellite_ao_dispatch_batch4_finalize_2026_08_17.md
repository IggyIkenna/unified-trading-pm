---
doc_type: plan
title: UI satellite AO batch 4 — finalize (upgrade source-doc citation + archive)
summary: >-
  Gated closeout for `ui_satellite_ao_dispatch_batch4_2026_08_17.md` — machine-held via `depends_on` + `gate_on_depends:
  true` until its 1 todo is done. Upgrades the source doc's already-flipped checkbox citation to real shipped evidence,
  then archives the batch doc via the standard 6-step ritual.
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ui, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/active/ui_satellite_ao_dispatch_batch4_2026_08_17.md,
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: deployment_and_user_management_master
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
depends_on: [ui_satellite_ao_dispatch_batch4_2026_08_17]
gate_on_depends: true
source: >-
  na-eligibility-audit 2026-08-17 RECLASSIFY-per-todo-split extraction, per `task_template.md` §4's
  finalize-plan-coverage rule.
assigned_role: infra
effort: low
sequential: true
drift_direction: advance-docs
context_scope:
  [
    /plans/active/ui_satellite_ao_dispatch_batch4_2026_08_17.md,
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
  ]
---

# UI satellite AO batch 4 — finalize

> **Machine-gated on `ui_satellite_ao_dispatch_batch4_2026_08_17.md`** (`depends_on` + `gate_on_depends: true`).
> `sequential: true` because the source-doc citation upgrade (todo 1) should land before archival (todo 2).

## Todos

- [ ] [REVIEW] P3. Once batch 4's todo lands, upgrade `data_status_tab_and_downloads_remediation_2026_06_16.md`'s
      Phase B checkbox citation from the bare extraction-pointer ("EXTRACTED 2026-08-17 ... to
      `ui_satellite_ao_dispatch_batch4_2026_08_17.md` item 1") to the real shipped evidence (`<repo>@<sha>` +
      `pw:L2 ✓`). Verify the shipped commit actually implements the denominator-freshness annotation before citing it
      — do not trust batch 4's own wording alone. Done when: the source doc's checkbox cites real shipped evidence.
      **Conflict-check (added 2026-08-18, plan_reconciler agt-2a424e)**:
      `ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md` todo 4 (still open) also reconciles/touches this same
      source doc's checkboxes for batch 1's work — currently NOT a live collision (todo 4's own 6 target items are
      already independently shipped `[x]` directly in the source doc, verified by plan_reconciler 2026-08-18), but
      coordinate or sequence if both finalize plans are ever worked concurrently.
- [ ] [DOC] P3. Archive `ui_satellite_ao_dispatch_batch4_2026_08_17.md` via the standard 6-step ritual once todo 1 is
      done: archive banner → codex-alignment check (none expected — small UI/backend feature) → fix every corpus
      referrer → confirm `locked_by` empty. Done when: the plan is moved to `plans/archive/2026_08/`, every referrer
      resolves to the new path, and this finalize doc archives alongside it in the same commit.

## Progress Log

- **context-scout 2026-08-20**: populated/refreshed context_scope (2 entries)
