---
doc_type: plan
title: CeFi satellite AO batch 2 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for cefi_satellite_ao_dispatch_batch2_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 17 of that plan's todos are done. Mirrors batch1-finalize's pattern (reconcile each distinct source
  doc's checkboxes independently once its batch-2 todo lands, then re-check the Deferred operator-gated/time-gated/
  human-only items for any that have since cleared), then archives batch2 via the standard 6-step ritual. Also carries
  the follow-up for batch2's 2 non-actioned findings (3 mistag retags + 1 archivable_now doc).
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch2_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched
  plan needs a companion gated finalize plan, mirroring the cefi batch1 + sports batch2-5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi satellite AO batch 2 — finalize

> **Machine-gated on `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 17 tasks in that plan are `done`. `sequential: true` because todo 2
> (deferred re-check) needs todo 1's reconciliation done first, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 17 distinct source docs' checkboxes.** For each of
      `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s now-done todos: flip the corresponding checkbox/section in its
      named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-2 commit(s) that shipped it —
      verify the actual shipped commit exists before citing it. For each source doc: after flipping, re-check whether it
      now has 0 open todos remaining (checkbox AND prose-form — do not trust checkbox count alone). Only flip a doc's
      `status` to `resolved` if it genuinely reaches 0 open todos. **Done when**: all 17 source-doc checkboxes/sections
      are flipped with verified evidence, and any doc that genuinely reaches 0 open todos is flipped to
      `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the 10 operator-gated + 1 time-gated + 1 human-only Deferred items from batch2's own
      doc**, now that time has passed and batch2's own todos have landed. For each of the 12 Deferred items: re-read the
      specific gating ground (operator decision, elapsed-time condition, or design-session need) to check if it has
      since cleared — if so, extract it as a new tracked todo in a follow-up `batch3` (do not draft it directly here,
      this finalize plan's own scope is reconciliation not fresh drafting); if still genuinely unresolved, leave it
      explicitly deferred (not speculative) — do not re-surface an already-asked operator question a second time, just
      note the re-check happened and it's still awaiting an answer. **Done when**: each of the 12 Deferred items has
      either (a) a note that it's ready for `batch3` extraction because its gate cleared, or (b) an explicit re-verified
      confirmation the gate is still open.
- [ ] [DOC] P2. **Action batch2's 2 non-batched findings.** (1) Retag the 3 mistagged docs named in batch2's "Note — 3
      mistags found" section (`breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`,
      `mtds_ungated_test_families_2026_07_17.md`, `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`)
      — read each doc's real content to decide the correct `asset_group` (likely `cross-cutting` or `meta` for all 3,
      confirm per-doc, do not assume), fix the frontmatter, and re-run
      `scripts/plan-hygiene/check_ag_closeout_linkage.py` after each retag (a doc just retagged can be newly orphaned
      within its NEW ag family if nothing there references it yet — add a one-line link to that ag's aggregated-sources
      digest if so). (2) Archive `cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md` (batch2's "Note — 1 doc
      found archivable_now") via the standard 6-step ritual. **Done when**: all 3 mistagged docs carry a corrected
      `asset_group` with `check_ag_closeout_linkage.py` passing 0 new orphans, and the archivable_now doc is moved to
      `plans/archive/2026_07/` with every corpus referrer fixed.
- [ ] [DOC] P1. **Archive `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved or re-confirmed all 12 — verify none silently vanish) → add the archive banner → run
      the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for
      every referrer of `cefi_satellite_ao_dispatch_batch2_2026_07_26` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
