---
doc_type: plan
title:
  TradFi registry/adapter correctness + honest-coverage residuals — finalize (reconcile + archive once fully closed)
summary: >-
  Housekeeping companion for `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` — gated via `depends_on` +
  `gate_on_depends: true` on that plan's own todos (Phase A2 + the still-open Phase C residue) being done, mirroring the
  finalize-plan-coverage rule's shape even though both plans are `assigned_vm: NA` (never AO-ingested — the gate is
  documentation of intent, same idiom the parent used pre-trim, not a live backlog hold). Because the target plan's
  todos are NATIVE (closed by direct work, or by a future AO-dispatch batch drafted off its content — e.g. a
  `/ag-closeout-audit` pass — rather than by AO workers dispatched against ITS OWN checkboxes), this is a LOCAL/human
  plan: whoever eventually closes out the last open item here picks this up to verify evidence, correct any sibling-doc
  checkbox that closure implies, and run the standard 6-step archival ritual. Archival is also gated on `depends_on` per
  PLAN_FORMAT.md ("`depends_on` documents task ordering + gates archival") — the target plan itself cannot archive
  before `tradfi_manifest_content_recovery_completion_2026_07_24.md` and
  `tradfi_backfill_throughput_followups_2026_07_24.md` are also done+archived, so this finalize's archival todo waits on
  all three, not just its direct target.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, close-out, registry, ao-readiness, archival, plan-hygiene]
related:
  [
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/archive/2026_07/tradfi_consolidated_closeout_history_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_registry_coverage_and_ao_readiness_2026_07_25]
gate_on_depends:
  true # documentation-only while both plans are assigned_vm: NA — same idiom as the target's own depends_on (never a
  # live backlog hold, since NA plans mint no backlog tasks). If the target is ever flipped to assigned_vm: planning
  # together with a matching flip here, the gate becomes a real dispatch hold with no further edits needed.
source: >-
  Authored alongside `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` per the orchestrating design pass's
  explicit instruction to give that child a companion finalize, adapted for its NA/local-only shape (its 3 sibling
  children from the 2026-07-24 3-way split do not carry one, since they are plain content relocations rather than
  AO-batch extractions — this doc exists because the design explicitly asked for it, not because the strict
  AO-dispatched finalize-plan-coverage rule mechanically requires it for a plan that stays NA).
assigned_role: data_engineering
sequential: true
drift_direction: none
---

# TradFi registry/adapter correctness + honest-coverage residuals — finalize

> **Gated on `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> documentation of intent while both plans stay `assigned_vm: NA`; pick this up once every todo in the target plan is
> closed (whether by direct work, or by a future AO-dispatch batch drafted off its content). `sequential: true` because
> todo 2 (reconcile) needs todo 1's verified evidence, and todo 3 (archive) must run last and additionally needs
> `tradfi_manifest_content_recovery_completion_2026_07_24.md` + `tradfi_backfill_throughput_followups_2026_07_24.md`
> (the target's own `depends_on`) to also be done+archived first, per PLAN_FORMAT.md's "`depends_on` gates archival"
> rule.

## Todos

- [ ] [REVIEW] P2. **Verify every todo in `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` is genuinely closed
      with real evidence** before touching any sibling doc: re-read each cited target
      (`tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`,
      `krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md` [archived, cite-only],
      `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` + its 2 sibling docs, the adapter dead-code audit's target
      issue doc, the shipped UAC/MTDS billing-entitlement-classification commit,
      `data_status_page_ux_and_canonicalisation_2026_07_16.md`, `distinct_values_noncanonical_audit_2026_07_20.md`,
      `tradfi_instrument_type_migration_read_stale_legacy_object_2026_07_17.md` +
      `phantom_captures_tradfi_2026_06_28.md` +
      `tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`, the KRX catalogue live-read, and the
      BLOCKED-INFRA Layer-1 catalogue-rebuild+promote evidence) and confirm the cited evidence is real (commit exists,
      report exists, live read shows what's claimed) — do not trust a todo's own "done" claim without re-verifying at
      least one hard fact per todo. Also cross-check whether any of these were instead closed via
      `tradfi_consolidated_native_ao_extract_2026_07_25.md`'s own AO-dispatched derivatives (todos 2-9 there target the
      same underlying facts) — if so, cite that plan's finalize evidence rather than re-verifying twice. **Done when**:
      each open todo in the target plan has a confirmed-real evidence citation recorded (or, for any that don't check
      out, a note that it's NOT actually done and should stay open, re-queued rather than falsely reconciled).
- [ ] [REVIEW] P2. **Reconcile every sibling doc's own checkbox that the target plan's closures imply** — for each todo
      verified done in the step above, flip/update the corresponding checkbox in its own named source doc (e.g.
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s capability-declaration note,
      `phantom_captures_tradfi_2026_06_28.md`'s diagnosis item), citing this plan's/the target's commit(s) as evidence.
      Also re-check the 2 non-dispatchable `[DESIGN]`/`[DECISION]` pointers (the `ohlcv_15m/24h` writer decision, the
      `mvp_mode` dead-gate decision) for whether either has since been ruled by the operator — if so, spin a new tracked
      todo/plan for the chosen direction rather than silently resolving it here. **Done when**: every sibling doc whose
      state changed via the target plan's closures has its own checkbox/note updated with a verified evidence citation,
      and both non-dispatchable design/decision pointers are re-checked for a cleared gate.
- [ ] [DOC] P2. **Archive both `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` and this finalize doc** via the
      standard 6-step archival ritual (per CLAUDE.md's plan-archival rule), gated on ALL of: (a) every todo in the
      target plan closed (todos 1-2 above); (b) `tradfi_manifest_content_recovery_completion_2026_07_24.md` AND
      `tradfi_backfill_throughput_followups_2026_07_24.md` (the target's own `depends_on`) also done+archived, per
      PLAN_FORMAT.md's "`depends_on` gates archival" rule — do not archive the target ahead of its own stated
      prerequisites even if its own todos are individually done. Steps: migrate any still-relevant DEFERRED items → add
      the archive banner → run the codex-alignment check → update `tradfi_consolidated_closeout_2026_07_18.md`'s "Phase
      A2 + Phase C — forked 2026-07-25" pointer section to reflect the closure → grep the corpus for every referrer of
      `tradfi_registry_coverage_and_ao_readiness_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty, confirm). **Done when**: both plans are moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and the parent's own pointer section is updated in the same commit.

## Codex SSOTs

No new durable contract is created by this plan — it reconciles and archives an already-scoped fork of
`tradfi_consolidated_closeout_2026_07_18.md`. `/codex/11-project-management/` (plan-archival ritual) is the standard
this finalize applies.
