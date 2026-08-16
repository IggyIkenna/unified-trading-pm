---
doc_type: plan
title: Cross-cutting satellite AO batch 2 — finalize (reconcile source docs + archive)
summary: >-
  Gated closeout for `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 22 todos are done. Reconciles each of the 6 distinct `instruments_master` source
  docs' checkboxes independently (citing the shipped commit per todo), then archives the batch doc via the standard
  6-step ritual.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    /plans/archive/2026_08/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cross_cutting_satellite_ao_dispatch_batch2_2026_08_09]
gate_on_depends: true
source: >-
  Satellite-batch-extraction sweep 2026-08-09, per `task_template.md` §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Cross-cutting satellite AO batch 2 — finalize

> **Machine-gated on `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 22 tasks in that batch are `done`.
> `sequential: true` because todo 2 (archival) must run after todo 1 (reconciliation).

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-08-16 (slot 10, data_engineering).** Reconciled all 6 distinct source docs'
      checkboxes against batch 2's now-done todos — flipped every `EXTRACTED 2026-08-09 → cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`
      pointer marker in each named source doc to a `DONE` citation of the batch commit(s) that shipped it, after
      verifying every cited SHA resolves as an ancestor of `origin/live-defi-rollout` (24 commits across 9 repos, all
      confirmed). Per-doc counts: `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (7),
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (6, incl. the already-`[x]` N5r/N6r item whose
      stale "EXTRACTED" text was corrected to name its actual shipped commits + the separate execution-tracking issue
      doc), `instruments_completion_tracker_2026_07_06.md` (4),
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (4),
      `plans/archive/2026_08/mvp_scope_catalogue_tagging_2026_06_08.md` (1, already archived — edited in place),
      `is_catalogue_g1_root_audit_log_2026_07_24.md` (1) — 23 markers total (the doc's own "22 items" count undercounted
      the already-checked N5r/N6r item). Re-checked each source doc for 0 remaining open todos (checkbox AND
      prose-form) — **caught a real trap**: `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`'s own
      summary read "DONE, 0 open ... ARCHIVE-READY" (a same-day plan_reconciler correction), and I initially started
      down the archival path on that basis, but its OWN dedicated finalize plan
      (`instruments_mtds_consistency_remediation_residuals_2026_07_24_finalize.md`) has independently re-confirmed on
      3 separate dispatches (2026-08-11×2/2026-08-12) that the "0 open" reading is a DELEGATION ARTIFACT, not genuine
      completion: N5r/N6r reads `[x]` only because it points to
      `/plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md`, whose own todo (e) — the
      live 133M-row prod apply+post-verify — is still `- [ ]` open (re-confirmed fresh 2026-08-16: no execution VM
      has run, no projection output exists). plan_reconciler's own finding explicitly caveated it never re-verified
      substance on individual `[x]` items. **Reverted the archival attempt** (banner + `status: complete` flip) and
      instead corrected the source doc's misleading summary text to name the delegation artifact + point at the
      dedicated finalize plan, per CLAUDE.md's "a doc that misled you is a finding — fix it in the same turn" rule.
      `status` left `active`; archival stays that finalize plan's job, not this todo's. The other 4 active source
      docs each carry genuine open work outside batch2's scope (gated/design items batch2 explicitly left untouched,
      per its own Progress Log) — `status` correctly left `active`. `mvp_scope_catalogue_tagging_2026_06_08.md` was
      already `status: complete` and archived — no status change needed. Done when: all source-doc checkboxes/sections
      flipped with verified evidence — satisfied (the status-flip sub-clause turned out to apply to 0 of the 6, not
      1, once the delegation-artifact trap was caught).
- [ ] [DOC] P1. Archive `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule) once todo 1 is done: add the archive banner → run the codex-alignment check
      (confirm no new durable contract from this batch) → grep the corpus for every referrer of this doc and fix each
      path to point at the archived location → clear `locked_by` (confirm already empty). Done when: the plan is moved
      to `plans/archive/2026_08/`, every corpus referrer resolves to the new path, and this finalize doc itself is
      archived alongside it in the same commit.

## Progress Log

- **context-scout 2026-08-15**: refreshed context_scope (4 entries) -- added the plan-completion-and-archival-
  discipline codex SSOT (todo 2's 6-step ritual cites "CLAUDE.md's plan-archival rule" but not the codex doc itself);
  kept the gated parent batch doc (has all 22 todos' `Source:` citations) plus the 2 of its 6 named source docs with the
  most citations (9 mentions each) -- the other 4 source docs (`instruments_completion_tracker_2026_07_06.md`,
  `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`, `mvp_scope_catalogue_tagging_2026_06_08.md`,
  `is_catalogue_g1_root_audit_log_2026_07_24.md`) are already discoverable via the batch doc's own per-todo `Source:`
  lines and this doc's `related:` frontmatter, so are not duplicated here.
- **2026-08-16 (slot 10, data_engineering) — todo 1 DONE.** Reconciled all 6 source docs against batch2's now-done
  todos. Confirmed batch2 itself is fully done (25/25 checkboxes `[x]`, fresh grep — no `- [ ]` remain), resolving an
  apparent contradiction in batch2's own Progress Log (a 2026-08-11 entry claimed the CME COMBO item was still `[ ]`;
  a fresh read today shows it `[x]` with a verified `instruments-service@dc8f13b914` citation — already resolved by
  the time this session started). Located every `EXTRACTED 2026-08-09 → cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`
  pointer marker across the 6 named source docs (they were already converted from checkboxes to bare-bullet extraction
  pointers at batch2-authoring time, not left as open `- [ ]` items — so the "flip the checkbox" instruction resolved
  to "replace the extraction pointer with a DONE citation" instead). Verified all 24 distinct commit SHAs cited by
  batch2 resolve as ancestors of `origin/live-defi-rollout` across 9 repos (deployment-service, deployment-api,
  deployment-ui, instruments-service, unified-api-contracts, e2e-testing, market-tick-data-service,
  unified-trading-system-ui, ml-service) before citing any of them. Edited all 23 markers (7+6+4+4+1+1) with DONE
  citations. **Near-miss caught mid-session**: almost archived
  `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` on its own "DONE, 0 open" summary text (a
  same-day plan_reconciler correction) before discovering its dedicated finalize plan
  (`instruments_mtds_consistency_remediation_residuals_2026_07_24_finalize.md`) had already, 3 times, correctly
  refused archival because N5r/N6r's "0 open" reading is a delegation artifact — the real VM-execution work
  (`/plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` todo (e)) is still open.
  Reverted the archive banner + status flip; corrected the misleading summary text in place instead. `status` left
  `active` on all 6 source docs — none reached genuine 0-open-todos in this pass. Todo 2 (archive batch2 + this
  finalize doc) is next, gated on this todo per `sequential: true` — not done in this dispatch per the
  one-task-per-session / don't-fan-out worker rule; left for the next dispatch of this plan.
