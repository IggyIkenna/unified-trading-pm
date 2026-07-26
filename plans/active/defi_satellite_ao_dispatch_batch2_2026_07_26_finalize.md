---
doc_type: plan
title: DeFi satellite AO batch 2 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch2_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 23 of that plan's todos are done. Mirrors batch1-finalize's pattern (reconcile each distinct source
  doc's checkboxes independently once its batch-2 todo lands, then re-check the Deferred conflict-gated/
  operator-gated/time-gated/too-large/human-only items for any that have since cleared), then archives batch2 via the
  standard 6-step ritual. Also carries the follow-up for batch2's 3 non-actioned findings (2 mistag retags + 1
  archivable_now doc).
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_satellite_ao_dispatch_batch2_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched
  plan needs a companion gated finalize plan, mirroring the defi batch1 + cefi batch2 + sports batch2-5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 2 — finalize

> **Machine-gated on `defi_satellite_ao_dispatch_batch2_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 23 tasks in that plan are `done`. `sequential: true` because todo 2
> (deferred re-check) needs todo 1's reconciliation done first, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all distinct source docs' checkboxes.** For each of
      `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s now-done todos: flip the corresponding checkbox/section in its
      named source doc(s) (each todo's text ends with "Source: `<doc>.md`" — 1 todo, the merged lst-rates-backfill one,
      cites TWO source docs, flip both), citing the batch-2 commit(s) that shipped it — verify the actual shipped commit
      exists before citing it. For each source doc: after flipping, re-check whether it now has 0 open todos remaining
      (checkbox AND prose-form — do not trust checkbox count alone). Only flip a doc's `status` to `resolved` if it
      genuinely reaches 0 open todos. **Done when**: all source-doc checkboxes/sections are flipped with verified
      evidence, and any doc that genuinely reaches 0 open todos is flipped to `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the 3 conflict-gated + 11 operator-gated + 3 time-gated + 1 too-large-or-risky + 2
      human-only Deferred items from batch2's own doc**, now that time has passed and batch2's own todos have landed.
      For each of the 20 Deferred items: re-read the specific gating ground to check if it has since cleared — if so,
      extract it as a new tracked todo in a follow-up `batch3` (do not draft it directly here, this finalize plan's own
      scope is reconciliation not fresh drafting); if still genuinely unresolved, leave it explicitly deferred (not
      speculative) — do not re-surface an already-asked operator question a second time, just note the re-check happened
      and it's still awaiting an answer. **Done when**: each of the 20 Deferred items has either (a) a note that it's
      ready for `batch3` extraction because its gate cleared, or (b) an explicit re-verified confirmation the gate is
      still open.
- [ ] [DOC] P2. **Action batch2's 3 non-batched findings.** (1) Retag
      `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` (batch2's "Note — 1 mistag found") — read
      the doc's real content to decide the correct `asset_group` (likely `cross-cutting` or `infra`, confirm), fix the
      frontmatter, and re-run `scripts/plan-hygiene/check_ag_closeout_linkage.py` after the retag. (2) Read
      `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` in full (batch2's "Note — a second mistag
      found during Phase-0 discovery") to resolve the defi-vs-cross-cutting ambiguity, check whether it is still
      `locked_by: live-defi-rollout` (if still locked, defer this sub-item to a later finalize iteration rather than
      editing a locked doc), and retag if the lock has cleared and the content confirms one side. (3) Archive
      `mtds_perp_funding_backfill_hang_2026_07_14.md` (batch2's "Note — 1 doc found archivable_now") via the standard
      6-step ritual. **Done when**: item (1) is retagged with `check_ag_closeout_linkage.py` passing 0 new orphans; item
      (2) is either retagged (lock cleared) or explicitly re-deferred with the lock status re-checked and cited; item
      (3) is moved to `plans/archive/2026_07/` with every corpus referrer fixed.
- [ ] [DOC] P1. **Archive `defi_satellite_ao_dispatch_batch2_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved or re-confirmed all 20 — verify none silently vanish) → add the archive banner → run
      the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for
      every referrer of `defi_satellite_ao_dispatch_batch2_2026_07_26` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
