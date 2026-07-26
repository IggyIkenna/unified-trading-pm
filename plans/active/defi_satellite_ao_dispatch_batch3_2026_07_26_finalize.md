---
doc_type: plan
title: DeFi satellite AO batch 3 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch3_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 12 of that plan's todos are done. Mirrors batch1/batch2-finalize's pattern (reconcile each distinct
  source doc's checkboxes independently once its batch-3 todo lands, then re-check the Deferred
  operator-gated/conflict-gated/non-batchable items for any that have since cleared), then archives batch3 via the
  standard 6-step ritual. Also carries the follow-up for batch3's non-actioned findings (2 archivable_now docs to
  archive + 1 exclude_cross_cutting mistag to confirm retagged). status: draft — activated only after its parent batch3
  is operator-approved and dispatched.
status: draft
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-3, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
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
depends_on: [defi_satellite_ao_dispatch_batch3_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26 (autonomous, scheduled ag_closeout_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan, mirroring the defi
  batch1 + batch2 + cefi + sports precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 3 — finalize

> **🟡 status: draft** — inert until its parent `defi_satellite_ao_dispatch_batch3_2026_07_26.md` is operator-approved
> (flipped to `active`) and dispatched. **Machine-gated on that plan** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 12 of its tasks are `done`. `sequential: true` because todo 2
> (deferred re-check) needs todo 1's reconciliation first, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all distinct source docs' checkboxes.** For each of
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s now-done todos: flip the corresponding checkbox/section in its
      named source doc (each todo ends with "Source: `<doc>.md`"), citing the batch-3 commit(s) that shipped it — verify
      the actual shipped commit exists before citing it. After flipping, re-check whether that source doc now has 0 open
      todos (checkbox AND prose-form — do not trust checkbox count alone); only flip its `status` to `resolved` if it
      genuinely reaches 0. **Done when**: all source-doc checkboxes/sections are flipped with verified evidence, and any
      doc that genuinely reaches 0 open todos is flipped to `status: resolved`.
- [ ] [REVIEW] P1. **Re-check batch3's Deferred items** (the operator-gated, conflict/sequence-gated, and 9
      non-batchable-orphan items), now that batch3's own todos have landed. For each: re-read the specific gating ground
      to check if it has cleared — if so, extract it as a new tracked todo in a follow-up `batch4` (do not draft it
      directly here — this finalize plan's scope is reconciliation, not fresh drafting); if still genuinely unresolved,
      leave it explicitly deferred and note the re-check happened (do not re-ask an already-open operator question).
      Specifically re-check: the E3 borrow leg (should clear once todo 4 A2-staking-leg lands), and the 5
      `defi_migration_audit_log` stale-premise items (need an operator reconciliation against the shipped shared-bucket
      architecture — confirm the premise is still stale, don't silently drop them). **Done when**: each Deferred item
      has either (a) a note it's ready for `batch4` extraction, or (b) an explicit re-verified confirmation the gate is
      still open.
- [ ] [DOC] P2. **Action batch3's non-batched findings.** (1) Archive the 2 archivable_now docs
      (`e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`, `mtds_perp_funding_backfill_hang_2026_07_14.md`)
      via the standard 6-step ritual — but FIRST confirm each still reaches 0 open todos on a fresh read (they were
      classified archivable_now 2026-07-26; re-verify nothing re-opened). (2) Confirm
      `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` got retagged off `[defi]` (batch2's finalize
      owns the retag; this is just a cross-check that it happened — if not, file/hand off, do not duplicate the retag
      todo). **Done when**: item (1)'s 2 docs are in `plans/archive/2026_07/` with every corpus referrer fixed (or
      explicitly re-deferred if a fresh read finds new open work); item (2) is confirmed done or handed off.
- [ ] [DOC] P1. **Archive `defi_satellite_ao_dispatch_batch3_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have resolved or re-confirmed all of them — verify none silently vanish) → add the archive banner → run the
      codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for every
      referrer of `defi_satellite_ao_dispatch_batch3_2026_07_26` and fix each path to point at the archived location →
      clear `locked_by` (already empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
