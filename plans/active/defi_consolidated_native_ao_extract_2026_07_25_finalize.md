---
doc_type: plan
title: DeFi consolidated native-todo AO extraction — finalize (reconcile + archive)
summary: >-
  Gated closeout for defi_consolidated_native_ao_extract_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 4 of that plan's todos are done. Reconciles each shipped todo's evidence back into
  defi_consolidated_closeout_2026_07_18.md's own native checkboxes (the ONLY source doc here — this extraction did not
  pull from any other satellite doc), re-checks the 2 staleness findings recorded in the extraction plan's Conflicts
  section to see whether they're now actionable, and archives the extraction plan once done.
status: active
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
last_updated: "2026-07-30"
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
context_scope:
  [
    /plans/active/defi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
    /plans/archive/issues/mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md,
  ]
---

# DeFi consolidated native-todo AO extraction — finalize

> **Machine-gated on `defi_consolidated_native_ao_extract_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 4 tasks in that plan are `done`. `sequential: true` because
> todo 3 (archival) must run last, after todos 1-2 land their findings.

## Todos

- [x] ✅ [REVIEW] P2. **DONE 2026-08-03 (slot-2, review craft).** Reconciled
      `defi_consolidated_closeout_2026_07_18.md`'s own native checkboxes for the 4 shipped todos: (1) Track 3's
      `--apply` nested item + the `[BACKEND] P1` parent (EXPECTED_SUBGRAPH_DEINDEXED) were **already flipped `[x]`** by
      a prior `na-eligibility-audit 2026-08-03` pass (line ~448) — verified, no further edit needed. (2)/(3) added the
      missing annotation to Track 8's `[INFRA] P1` cron-resume item noting the "honest-coverage-nightly right-size"
      sub-clause is now DONE (citing `instruments-service@12825e81` + `deployment-service@fec7946`/`d880de3`, all
      verified live via `git log --oneline -1`), while leaving the todo itself open (cron-resume still gated on
      Track-1/2 + the migration VM) — the codex-drift-doc sub-clause also stays open. (4) The bottom-of-file `[DOC] P1`
      digest-entry todo was **already flipped `[x]`** 2026-07-28 (slot 8) — verified, no further edit needed. Evidence:
      this commit's diff to `defi_consolidated_closeout_2026_07_18.md` (Track 8 annotation) in `unified-trading-pm`.
- [x] ✅ [DIAG] P3. **Re-check the 2 staleness findings — BOTH RESOLVED 2026-08-05 (slot-9, data_engineering).** (a)
      `issues/defi_adapter_dead_code_audit_2026_07_24.md` IS the complete, current answer to Track 8's "audit defi
      adapters" native todo — the closeout doc's checkbox at line 626 is **already flipped `[x] ✅`** (resolved
      2026-08-01, citing the audit doc + batch7 incremental re-verification). No further action needed — the staleness
      finding was correct on 2026-07-25 but independently resolved since. (b) Tick 3 addendum does NOT contain a
      concrete, scoped design for a standalone manifest-row-level purge — it recommends either (a) a one-off delete of 9
      specific stale `_index` rows keyed on old glued `instrument_id`s, or (b) confirming whether a full-corpus rebuild
      regenerates from scratch — neither is a general purge mechanism. However, the closeout doc's glued-id todo at line
      736 is **already flipped `[x] ✅`** (resolved 2026-08-01): all 19 remaining rows confirmed phantom, folded into
      the existing `:401` P0 purge. Still unscoped as a standalone mechanism, but moot — the rows have a disposition
      path. No new candidate item to draft. **Evidence**: `unified-trading-pm` plan-only edit (this flip).
- [ ] [DOC] P3. **Archive `defi_consolidated_native_ao_extract_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm no remaining Deferred items need migrating (this plan's Deferred table is
      a reference classification, not open work — verify none of it silently needs a new todo) → add the archive banner
      → run the codex-alignment check (none expected — no new durable contract) → grep the corpus for every referrer of
      `defi_consolidated_native_ao_extract_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: re-verified context_scope (4 entries) -- unchanged, already the minimal set covering
  both open reconcile/archive todos (source docs cited by the open Re-check + Archive steps).
