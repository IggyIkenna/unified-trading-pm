---
doc_type: plan
title: TradFi satellite AO batch 4 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch4_2026_07_26.md — machine-held via depends_on plus
  gate_on_depends: true until all 8 of that plan's todos are done. Mirrors the batch1/batch2/batch3-finalize pattern:
  reconcile each distinct source doc's checkboxes and prose sections once its batch-4 todo lands (three of batch4's
  source docs are PROSE-ONLY with zero checkboxes, so this reconciliation must check prose too, not just checkbox
  counts), then re-check batch4's own Deferred conflict-gated / too-large-or-risky items for any that have since
  cleared, then archive batch4 via the standard 6-step ritual. Stays `status: draft` until batch4 itself is approved and
  dispatched, per task_template.md section 4's finalize-plan-coverage rule.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_satellite_ao_dispatch_batch4_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit tradfi run 2026-07-26 (autonomous mode), per task_template.md section 4's finalize-plan-coverage
  rule — every AO-dispatched plan needs a companion gated finalize plan, mirroring the tradfi batch1/batch2/batch3 plus
  cefi batch2/3, defi batch2, and sports batch2-5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# TradFi satellite AO batch 4 — finalize

> **Status: draft.** This finalize plan stays draft until `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` is itself
> approved and flipped to `active` by the operator — flipping either one is an operator decision, never autonomous.
>
> **Machine-gated on `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md`** (`depends_on` plus `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 8 tasks in that plan are `done`. `sequential: true` because
> todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-4, review-craft).** Verified all 8 batch4 source docs against the batch4
      plan's own evidence text (commits spot-checked reachable: `instruments-service@fc07e6b6`,
      `unified-trading-pm@377efc33b`, `@935de9424`, `@1dd1a22fd`). Five of the 8 were already correctly reconciled
      in-doc by their executing workers (`tradfi_t1_no_working_mtds_job` — `status: resolved`;
      `tradfi_legacy_bucket_deleted_without_also_legacy_migration` — `status: resolved`, dates corrected;
      `tradfi_fx_provenance_and_manifest_id_defects` — write-path fix + comment-currency landed, `status: open`
      correctly reflects the genuine remaining historical-backfill todo; `tradfi_sp500_ml_and_arb_backtest_readiness` —
      3 stale BLOCKED- premises re-scoped; `data_completion_tradfi_2026_07_15` — coverage table + base-library.sh
      checkbox recorded). Found and fixed 2 real gaps matching this batch's own "prose-only trap" warning that had NOT
      been closed: (1) `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s Path-B `_default_csv_path()` residual
      (batch4 todo 4) was fixed in code (`instruments-service@fc07e6b6`) but its own prose still read "not fixed here —
      out of this todo's scope" — corrected the prose in-place (no checkbox touched, per batch4's own scope guard) to
      state the fix + citation; (2) `tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`'s corresponding closeout
      digest line still read "0 open todos" — the exact trap this batch names — corrected to list its 4 real 2026-07-27
      follow-up todos. Also found and fixed a THIRD, adjacent staleness this todo's "for every source doc, re-check
      0-open-items" instruction covers: `/plans/archive/issues/tradfi_docs_reconciliation_findings_2026_07_21.md` is
      fully resolved (35/35 findings applied, archived 2026-07-28) but the closeout's aggregated-source digest still
      listed its 3 findings (P1 L97/L460/L237) as open — corrected to 0-open with the resolution citation. All edits
      shipped in `unified-trading-pm` (this commit): `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`,
      `tradfi_consolidated_closeout_2026_07_18.md`. No doc carried a non-empty `locked_by`; no doc's `status` was
      flipped to `resolved` by this todo (the 2 already `resolved` were flipped by their own executing workers, verified
      correct as-is). **Reconcile all 8 distinct source docs — checkboxes AND prose.** For each of
      `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md`'s now-done todos, flip or update the corresponding
      checkbox/section in its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-4
      commit(s) that shipped it — verify the actual shipped commit exists before citing it. **This batch is unusual and
      the reconciliation must reflect it**: three of the source docs
      (`issues/tradfi_t1_no_working_mtds_job_2026_07_17.md`,
      `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`, and the prose residual in
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`) carry their remaining work as PROSE with zero checkboxes,
      which is exactly why the consolidated closeout's aggregated-source digest reported them as "0 open todos". So for
      each of those three, confirm the batch-4 todo left behind either a real canonical `- [ ] [TAG] P<N>.` todo or a
      `status: resolved` frontmatter — never prose-only remaining work — and correct the corresponding digest line in
      `tradfi_consolidated_closeout_2026_07_18.md` in the same commit. For every source doc: after reconciling, re-check
      whether it now has 0 open items (checkbox AND prose — do not trust checkbox count alone). Only flip a doc's
      `status` to `resolved` if it genuinely reaches 0 open items, and never touch a doc carrying a non-empty
      `locked_by`. **Done when**: all 8 source docs are reconciled with verified evidence, the three prose-only docs no
      longer hide work from a checkbox grep, the closeout's digest lines for them are corrected, and any doc that
      genuinely reaches 0 open items is flipped to `status: resolved`.

- [ ] [REVIEW] P1. **Re-check batch4's own Deferred sections now that time has passed** — the 2 conflict-gated items
      (the `_tradfi-ohlcv-launcher-lib.sh` fan-out collision between the throughput doc and batch2 todo 3; the
      two-claimant `[CODE] P1` checkbox on the DNS-starvation issue doc) and the 1 too-large-or-risky item
      (`tradfi_manifest_content_recovery_completion_2026_07_24.md`). For each: re-read the specific gating ground to
      check whether it has since cleared — if the operator has ruled, or one side has shipped, or a dated section proves
      one claim stale, extract it as a new tracked todo in a follow-up `batch5` (do NOT draft it directly here); if
      still genuinely unresolved, leave it explicitly deferred and do NOT re-ask an already-asked operator question.
      Also cross-reference `tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`'s own deferred re-check rather
      than duplicating it. **Done when**: each of the 3 Deferred items has either (a) a note that it is ready for
      `batch5` extraction because its gate cleared, or (b) an explicit re-verified confirmation the gate is still open,
      with the evidence cited.

- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved or re-confirmed all 3 — verify none silently vanish) → add the archive banner → run
      the codex-alignment check (batch4 creates no new durable contract beyond todo 7's edit to
      `/codex/02-data/canonical-cutover-register.md`; confirm that edit landed and is consistent) → grep the corpus for
      every referrer of `tradfi_satellite_ao_dispatch_batch4_2026_07_26` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself is archived
      alongside it in the same commit.

## Codex SSOTs

No new durable contract is created by this plan. `/codex/11-project-management/` carries the archival ritual;
`plans/PLAN_FORMAT.md` carries the `status: draft` and `gate_on_depends` semantics this plan relies on.
