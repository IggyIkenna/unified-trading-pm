---
doc_type: plan
title: DeFi satellite AO batch 7 — finalize (reconcile source docs + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch7_2026_08_01.md — machine-held via depends_on + gate_on_depends:
  true until all 4 of that plan's todos are done. Mirrors batch1-6-finalize's pattern: reconcile each of the 2 distinct
  source docs' checkboxes independently once their batch-7 todo(s) land, re-check the 2 Deferred conflict-found items
  for whether their blocking claim has since cleared, then archive batch7 via the standard 6-step ritual.
status: complete # (was: active) 2026-08-02 archival sweep: all 3 todos [x], no locked_by
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-7, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch7_2026_08_01.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch7_2026_08_01.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
depends_on: [defi_satellite_ao_dispatch_batch7_2026_08_01]
gate_on_depends: true
source: >-
  `/na-eligibility-audit defi` run 2026-08-01 (autonomous, scheduled na_eligibility_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 7 — finalize

> **🟢 ARCHIVED 2026-08-02.** All 3 todos done: source-doc reconciliation (todo 1), Deferred-item re-check (todo 2 — the
> `cd` bug confirmed shipped, the QG-harness finding resolved-no-action on code evidence), and this archival itself
> (todo 3) — alongside `defi_satellite_ao_dispatch_batch7_2026_08_01.md`, archived in the same commit.

**status: active — gated on batch7's 4 todos via `depends_on` + `gate_on_depends: true`; the dispatcher will not release
these until batch7 is fully done.**

## Todos

- [x] ✅ [DOC] P1. Once all 4 of `defi_satellite_ao_dispatch_batch7_2026_08_01.md`'s todos are `[x]`, reconcile each of
      the 2 distinct source docs (`defi_consolidated_closeout_2026_07_18.md` — 3 of the 4 todos;
      `issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md` — the 4th) — flip/annotate their own
      checkboxes with the batch-7 commit SHA, so a doc read independently (outside this batch) shows accurate state.
      Repo: unified-trading-pm. Done when: both source docs show an annotation citing the batch-7 todo + commit SHA that
      closed their item. — **DONE 2026-08-02 (slot-13)**: of the closeout doc's 3 items, 2 (dead-code audit, glued-id
      re-verify) were already flipped `[x]` by prior batch-7 work; the 3rd (curve_adapter ARB/POLY RPC wiring) was still
      `[ ]` with only a "track completion, close by citation" pointer — flipped to `[x] ✅` with the shipped SHA
      (`market-tick-data-service@1f58a127`). The issue doc's 4th item (ManifestWriter `per_vm_shards` audit) was already
      flipped `[x]` DONE 2026-08-02 (slot-14) with the full 3-repo-SHA citation — no action needed. Both source docs now
      show accurate state read independently.
- [x] ✅ [DOC] P2. Re-check the 2 Deferred conflict-found items (the `setup-data-pipeline-vm.sh` canonical-migration
      `cd` bug parked on `defi_consolidated_native_ao_extract_2026_07_25.md`'s in-progress claim; the "QG HARNESS
      collects the wrong test suite" finding parked on `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s
      under-evidenced verdict) — if the native-extract plan's fix has since shipped, or a scoping read has since
      evidenced the QG-harness finding, resolve/close the parked note (fold into a batch8 todo if new bounded work
      results; otherwise mark resolved-no-action). Repo: unified-trading-pm. Done when: both parked items have an
      explicit resolved/still-open verdict recorded. — **DONE 2026-08-02 (slot-13)**: (1) the native-extract `cd` bug —
      confirmed SHIPPED, both sub-steps `[x] ✅ DONE 2026-07-28 (slot-13, infra)` in
      `defi_consolidated_native_ao_extract_2026_07_25.md`, fix at `deployment-service@0ed2ca6`; annotated the resolution
      onto batch7's own Deferred note. (2) the QG-harness hollow-sentinel finding — did a code scoping read (not a live
      repro; `uv run pytest --collect-only` stalled >90s on this host's stale `.venv`, unrelated shared-host contention)
      of `scripts/quality-gates-base/qg-common.sh`: a WORKTREE-IDENTITY GUARD shipped 2026-07-24 now hard-fails on the
      exact `PROJECT_ROOT`-vs-actual-git-toplevel mismatch class this finding's root-cause note names, converting the
      original silent "collected 6 items, exits 0" hollow-pass into a loud `exit 1` — verdict **RESOLVED-NO-ACTION on
      code evidence**, annotated + checkbox flipped on the source doc (`defi_migration_audit_log_2026_07_24.md:577`); no
      new bounded work to fold into batch8.
- [x] ✅ [DOC] P1. Archive `defi_satellite_ao_dispatch_batch7_2026_08_01.md` via the standard 6-step ritual (migrate any
      residual DEFERRED items → banner → codex-alignment check → update CLAUDE.md/codex on any new contract → update
      every referrer's path corpus-wide → clear lock). Repo: unified-trading-pm. Done when: batch7 is in
      `plans/archive/2026_08/` with a superseded_by/archived banner and zero remaining referrers to its old
      `plans/active/` path. — **DONE 2026-08-02 (slot-13)**, 6-step ritual: (1) both Deferred items already fully
      resolved by todo 2 above (cd bug shipped elsewhere, QG-harness resolved-no-action) — nothing residual to migrate
      into a new todo. (2) archived-banner added to both this doc and batch7 itself, `status: complete` set on both. (3)
      codex-alignment check: this finalize's own work is pure doc-reconciliation + a code-evidence scoping read, no new
      code/behavior/contract shipped — no codex doc needs updating. (4) same conclusion — no new contract for
      CLAUDE.md/codex to record. (5) updated every prose pointer-citation corpus-wide to the `plans/archive/2026_08/`
      path: `defi_consolidated_closeout_2026_07_18.md`,
      `issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`,
      `issues/defi_adapter_dead_code_audit_2026_07_24.md`,
      `issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md`, `defi_migration_audit_log_2026_07_24.md`
      (finalize-doc citation). Left untouched: `INDEX.md` (auto-generated, regenerated via script below, not
      hand-edited), `plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md` (frozen historical snapshot),
      `codex/02-data/availability-manifest-and-data-status.md` (already cited the forward-looking archive path). (6) no
      lock existed (`locked_by:` empty on both docs); `git mv` both docs to `plans/archive/2026_08/` in the same commit,
      re-ran `scripts/plans/regenerate_active_plan_index.py` to drop both from `INDEX.md`.

## Progress Log

- 2026-08-01 (slot-7, scheduled `na_eligibility_auditor`): Drafted alongside batch7, both `status: active`, gated on
  batch7's 4 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting on batch7's todos to land.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- 2026-08-02 (slot-13): Todo 1 — reconciled both source docs (curve_adapter checkbox was the only one still open;
  flipped with the shipped SHA). Todo 2 — the native-extract `cd` bug is confirmed SHIPPED
  (`deployment-service@0ed2ca6`); the QG-harness hollow-sentinel finding got a code scoping read (a live
  `--collect-only` repro attempt stalled on this slot's stale `.venv`, unrelated host contention) that found the
  2026-07-24 worktree-identity guard in `qg-common.sh` already converts the finding's silent-hollow-pass failure mode
  into a loud `exit 1` — verdict RESOLVED-NO-ACTION, annotated on `defi_migration_audit_log_2026_07_24.md:577`. Todo 3 —
  ran the 6-step archival ritual on both this doc and batch7 itself; `git mv` to `plans/archive/2026_08/`, INDEX.md
  regenerated.
