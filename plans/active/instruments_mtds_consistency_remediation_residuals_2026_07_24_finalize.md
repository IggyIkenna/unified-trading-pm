---
doc_type: plan
title: Instruments <-> MTDS F1-N9 consistency remediation residuals — finalize
summary:
  Gated finalize companion for instruments_mtds_consistency_remediation_residuals_2026_07_24.md (operator ruling
  2026-07-24 requirement) — reconciles N5r/N6r + N1b evidence back into the source doc once both land, then runs the
  6-step archival ritual once the source doc has zero open todos.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [finalize, archival, instruments, mtds, manifest]
related: [instruments_mtds_consistency_remediation_residuals_2026_07_24]
created: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
effort: medium
drift_direction: none
depends_on: [instruments_mtds_consistency_remediation_residuals_2026_07_24]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Authored 2026-08-09 to satisfy task_template.md's "every AO-dispatched plan needs a gated finalize plan" rule
  (operator ruling 2026-07-24) — the source doc was reclassified assigned_vm: NA -> planning this same session once the
  operator ruled on its two remaining operator-gated items (N5r/N6r, N1b), and the finalize-plan-coverage QG gate
  correctly caught the missing companion before commit.
context_scope:
  [
    /plans/archive/2026_08/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/task_template.md,
  ]
last_updated: "2026-08-09"
---

# Instruments <-> MTDS F1-N9 consistency remediation residuals — finalize

## Todos

- [x] ✅ [REVIEW] P2. Once both of the source doc's remaining todos (N5r/N6r DeFi manifest rebuild-for-real-replace, N1b
      CEFI ~698k-row reclassify) are done, reconcile their evidence back into
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`'s own checkboxes — re-verify the cited
      commit/manifest-state exists, don't trust a copied evidence line. Also re-check N1b's Step-4 enumerator dependency
      (flagged as unverified at ruling time) actually cleared before treating it as done. **DONE 2026-08-11 (slot 17)**:
      both items' checkboxes in the source doc already carry inline evidence from the sessions that worked them (not a
      copied summary) — re-verified rather than trusted: **N1b** — `instruments-service@097e230b`, `@8cf44c66`,
      `@159c0ebe`, and `unified-trading-library@a35819ee` all confirmed present in `git log --oneline` on this checkout;
      Step-4's catalogue dependency is independently confirmed cleared (source doc's own 2026-08-09 slot-6 note: "7/7
      empty_confirmed" verified merged). **N5r/N6r** — the source doc's own checkbox claims only EXTRACTION (not
      completion) to `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`; confirmed that doc genuinely exists and
      carries the N5r/N6r item. **Correction found during this re-verification**: the batch2 doc's own N5r/N6r checkbox
      is marked `[x]` but its own body text says "this checkbox stays open until (e)'s live re-audit confirms 0 stale
      rows" — a live contradiction. The linked execution issue doc
      (`issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md`) confirms sub-step (e) (the actual prod
      apply) is still genuinely `[ ]` open as of 2026-08-10T21:3x — that checkbox mismatch in the batch2 doc is a
      pre-existing defect in a DIFFERENT, still-active doc, out of this finalize plan's scope to fix; not blocking here
      because the source doc being archived never claimed N5r/N6r was DONE, only extracted — the real remaining work
      (sub-step e) is tracked live in the still-open execution issue doc, not silently dropped. Also migrated a
      prose-only deferral found during this pass (the source doc's 2026-07-13 "who executed the undocumented legacy
      delete" follow-up, never a tracked todo) into
      `issues/undocumented_legacy_gcs_delete_provenance_2026_08_11.md` per the archival-discipline "todos not prose"
      rule, before archiving the doc that carried it.
- [ ] [DOC] P2. Once the source doc shows zero open todos, run the standard 6-step archival ritual on it
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — migrate any deferred item, banner,
      codex-alignment check, corpus-wide referrer fixup, then `git mv` to `plans/archive/<YYYY_MM>/`. Distinct
      `[TAG]`/priority from the REVIEW todo above (per task_template.md's same-tag-collision gotcha).
