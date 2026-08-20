---
doc_type: plan
title: >-
  cefi_deribit_binance_futures_bundle_verification_2026_06_20 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for cefi_deribit_binance_futures_bundle_verification_2026_06_20.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched todos ship (citing each landing commit), then archives it via the standard 6-step ritual once fully
  closed. Authored 2026-07-27 as part of na_docs_validity_and_ao_eligibility_audit_2026_07_26.md's Phase 1
  reclassification pass, per task_template.md's finalize-plan-coverage rule (every assigned_vm:planning plan needs a
  companion gated finalize plan).
status: active
nature: process
asset_group: [cefi, defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-27"
last_updated: "2026-08-03"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
archive_exempt: true # gate_on_depends:true finalize doc — stays active by design until the parent's DERIBIT gap closes (see Progress Log)
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_deribit_binance_futures_bundle_verification_2026_06_20]
gate_on_depends: true
source: >-
  na_docs_validity_and_ao_eligibility_audit_2026_07_26.md Phase 1 (2026-07-27) --
  cefi_deribit_binance_futures_bundle_verification_2026_06_20.md was reclassified assigned_vm:NA -> planning after
  verifying its remaining open todos are bounded/deterministic and conflict-free against currently-active AO plans; this
  finalize doc closes the finalize-plan-coverage gate the reclassification itself triggered.
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md,
    /plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
  ]
---

# cefi_deribit_binance_futures_bundle_verification_2026_06_20 — finalize

## Todos

- [x] ✅ [REVIEW] P2. **DONE 2026-07-31 (slot-12, cicd/review craft) — reconciled; source plan intentionally NOT
      archived, real residual work remains.** All 7 of
      `cefi_deribit_binance_futures_bundle_verification_2026_06_20.md`'s own todos were already `[x]` with evidence
      (VERIFY findings + the 2026-06-24 backfill relaunch + 2026-07-30 spot-checks) — nothing to flip there, and each
      checked item accurately reflects the action taken at the time, not a false-progress claim. **Confirmed residual
      work IS still open**, however, outside this plan's own checkbox set: the source plan's own "Success criteria"
      requires "every (venue, data_type, day) cell is `captured`, honestly `empty_confirmed`/`expected_unattempted`, or
      has a genuine-gap backfill that ran to completion" — that bar is NOT met for DERIBIT
      `options_chain`/`futures_chain`. Per `issues/deribit_options_chain_af_g4_blocker_2026_07_03.md` (still
      `status: open`, last re-verified 2026-07-29/30): `options_chain` 113,615 `attempted_failed`/1 captured,
      `futures_chain` 112,728/0 — essentially unchanged since 2026-07-15, gated on the Track-2 coverage backfill
      actually capturing the underlying per-symbol data (the 2026-06-24 relaunch this plan's own SCRIPT P0 cites wrote
      `book_snapshot_5`/`trades`, not this bundle). Track-2 itself
      (`plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) is NOT done: its backfill VM
      (`cefi-queue-heavy-binancefutu-x17-20260727-210013`) was **preempted 2026-07-28T10:51 UTC and never recovered**
      (~2.3% of the target span processed — see that plan's 2026-07-30 Progress Log entry +
      `issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`), and its 2 POST-BACKFILL gate todos
      (`-004`/`-005`) are durably parked on `cefi-track2-backfill-vm-terminated=false` pending recovery. **Decision (per
      this todo's own fork): leave `cefi_deribit_binance_futures_bundle_verification_2026_06_20.md` `status: active` —
      do NOT force-archive it.** Added a cross-reference banner there pointing at this finding. **This finalize plan is
      ALSO NOT archived**, despite its own only todo now being `[x]`: archiving it would remove the sole active plan
      gating `cefi_deribit_binance_futures_bundle_verification_2026_06_20` (`assigned_vm:planning`, 7 todos, not itself
      a finalize plan) via `depends_on`+`gate_on_depends: true`, which would regress
      `scripts/quality_gates/check_finalize_plan_coverage.py`'s coverage baseline (no other active plan gates that
      slug). This doc stays in `plans/active/`, `status: active`, purely to keep serving that structural gate until the
      residual closes. **Re-check trigger tracked as a real todo** (not left as prose): added todo 4 to
      `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md` (machine-gated on Track-2's own 5 todos being
      `done`) to re-verify the DERIBIT gap and complete this deferred close-out once Track-2 genuinely finishes.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (6 entries) unchanged — `_finalize` gate doc, no source-code
  paths added per the skip-source carve-out; all 6 entries confirmed resolving on disk.
