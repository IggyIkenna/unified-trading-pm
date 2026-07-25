---
doc_type: plan
title: DeFi consolidated native-todo AO extraction — finalize (reconcile + archive)
summary: >-
  Gated closeout for defi_consolidated_native_ao_extract_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 4 of that plan's todos are done. Reconciles each shipped todo's evidence back into
  defi_consolidated_closeout_2026_07_18.md's own native checkboxes (the ONLY source doc here — this extraction did not
  pull from any other satellite doc), re-checks the 2 staleness findings recorded in the extraction plan's Conflicts
  section to see whether they're now actionable, and archives the extraction plan once done.
status: draft
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, native-extract, archival]
related:
  [
    /plans/active/defi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_consolidated_native_ao_extract_2026_07_25]
gate_on_depends: true
source: >-
  Per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize
  plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi consolidated native-todo AO extraction — finalize

> **Machine-gated on `defi_consolidated_native_ao_extract_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 4 tasks in that plan are `done`. `sequential: true` because
> todo 3 (archival) must run last, after todos 1-2 land their findings.

## Todos

- [ ] [REVIEW] P2. **Reconcile `defi_consolidated_closeout_2026_07_18.md`'s own native checkboxes** for the 4 shipped
      todos: (1) flip the Track 3 `--apply` nested item + verify the Track 3 `[BACKEND] P1` parent
      (EXPECTED_SUBGRAPH_DEINDEXED) now has zero remaining sub-items and can be flipped to `[x]` too; (2)/(3) note in
      Track 8's prose that the "honest-coverage-nightly right-size" portion of its `[INFRA] P1` cron-resume item is now
      addressed (do NOT flip that whole todo — the cron-resume action itself is still gated on Track 1 and stays open;
      only annotate that its right-size sub-clause is done, citing the shipped commit); (4) flip the bottom-of-file
      `[DOC] P1` digest-entry todo. Verify the actual shipped commit(s) exist before citing them
      (`git log --oneline -1 <sha>` in the relevant repo). **Done when**: all 4 corresponding checkboxes/annotations in
      `defi_consolidated_closeout_2026_07_18.md` accurately reflect the shipped state, each citing its real commit sha.
- [ ] [DIAG] P3. **Re-check the 2 staleness findings recorded in the extraction plan's "Conflicts / staleness found"
      section for whether they're now independently actionable.** (a) Re-verify whether
      `issues/defi_adapter_dead_code_audit_2026_07_24.md` is still the complete, current answer to Track 8's "audit defi
      adapters" native todo (line ~609) — if so, flip that native checkbox to `[x]` citing the audit doc directly (this
      is a pure staleness correction, not new work, so it's safe to do here even though it wasn't part of the gated
      extraction plan's own scope); if a NEWER audit superseded it, note that instead. (b) Re-read
      `plans/archive/issues/mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md` addendum "tick 3" in full —
      if it now contains (or a sibling doc now contains) a concrete, scoped design for the "manifest-row-level purge" it
      recommends, draft a scoped `defi_satellite_ao_dispatch_batch2`-style candidate item for it (with the standard
      finding-O delete/apply tagging, since a manifest-row purge is real prod-manifest mutation); if it's still
      unscoped, record that and leave it for a future check. **Done when**: both (a) and (b) have an explicit recorded
      verdict (fixed-here / still-stale / now-scoped-into-a-new-candidate), with (a)'s checkbox flip actually applied if
      warranted.
- [ ] [DOC] P3. **Archive `defi_consolidated_native_ao_extract_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm no remaining Deferred items need migrating (this plan's Deferred table is
      a reference classification, not open work — verify none of it silently needs a new todo) → add the archive banner
      → run the codex-alignment check (none expected — no new durable contract) → grep the corpus for every referrer of
      `defi_consolidated_native_ao_extract_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
