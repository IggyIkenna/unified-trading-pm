---
doc_type: plan
title: CeFi satellite AO batch 5 — finalize (reconcile source docs + close the deferral + archive)
summary: >-
  Gated closeout for cefi_satellite_ao_dispatch_batch5_2026_08_02.md — machine-held via depends_on + gate_on_depends:
  true until all 5 of that plan's todos are done. Mirrors the batch1 through batch4 finalize pattern: reconcile each
  source doc's checkboxes once its batch-5 todo lands, re-check batch5's single Deferred item (the KEEP-NA-ruled
  marker-format prod migration) for a cleared gate, close the one corpus gap batch5 identified but deliberately did not
  fix mid-batch (the bitfinex/bitget reclassified doc has no paired finalize sibling), then archive batch5 via the
  standard 6-step ritual.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch5_2026_08_02.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize.md,
    /plans/active/issues/execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.35
estimate_calibrated_ai_days: 0.28
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch5_2026_08_02]
gate_on_depends: true
source: >-
  Operator interactive Q&A 2026-07-30 (the same session that authorized batch5), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan, mirroring the cefi
  batch1 through batch4 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch5_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
---

# CeFi satellite AO batch 5 — finalize

> **Machine-gated on `cefi_satellite_ao_dispatch_batch5_2026_08_02.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 5 tasks in that plan are `done`. `sequential: true` because the
> archival todo must run last and depends on the reconciliation todos ahead of it.

> **Distinct `[TAG] P<n>.` prefixes on every todo below** — deliberately, per `task_template.md` § 4's 2026-07-31
> finding: when the self-archival todo lands in the SAME commit as its own `git mv`, the AO done-gate's tag+priority
> disambiguator fails CLOSED if two checked lines share a prefix.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 4 source docs' checkboxes against the landed batch-5 todos.** —
      unified-trading-pm@3632a17b4. All commits verified on origin/live-defi-rollout. Source-doc status: -
      `mtds_live_smoke_vm_not_tardis_guarded`: all 3 checkboxes done (P1+P2 NOT-A-BUG, P3 shipped @509b2553c) →
      **resolved**, 0 remaining. - `mdps_backfill_cefi_trades_gap_fill_completion`: both checkboxes done (manifest merge
      shipped, IAM fixed) → **resolved**, 0 remaining. - `cefi_consolidated_vm_aster_data_landing_recheck`: batch5's
      third P3 done (liquidations NOT-A-BUG); 2 remaining open (batch4's P2+P3 gcloud checks) — NOT resolved. -
      `cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans`: batch5's P3 done (catalogue-completeness:
      id-form mismatch); 1 remaining open (Deferred P2 marker-format migration, still BLOCKED-OPERATOR-DECISION) — NOT
      resolved. Each cited SHAs reachable on origin: ✅. Remaining-open counts explicitly stated: ✅.

- [x] ✅ [REVIEW] P2. **Re-checked batch5's single Deferred item — gate still blocked (2026-08-05, slot 8).** The
      deferred item is
      `/plans/active/issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`'s
      `[DATA] P2` marker-format prod migration (~700 unmigrated manifest ids across BYBIT raw-date dated futures,
      COINBASE-FUTURES PERPETUAL, BITGET-FUTURES PERPETUAL), ruled KEEP-NA on 2026-07-30 for lacking the delete/apply
      gate. **Re-verification 2026-08-05**: re-read the issue doc live — the P2 todo remains unchecked, the doc is still
      `assigned_vm: NA`, no `[OPERATOR]` tag with a delete-safety cite has been added, no
      `gcs_bucket_soft_delete_retention_seconds()` ≥ 604800s reversibility check has been recorded for the target
      bucket, and the latest na-eligibility-audit (2026-08-04) reaffirmed KEEP-NA. **Gate has not cleared.** When it
      does clear (either via an `[OPERATOR]` tag with a delete-safety cite per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3a, or a fresh same-run reversibility check), the
      ~700-id migration is a natural batch6 candidate — do not draft it here (this finalize plan's scope is
      reconciliation, not fresh drafting). **Batch5's own P3 catalogue-completeness todo** (slot 5, 2026-08-05, resolved
      at unified-trading-pm@766822efe) found 10 legacy Kraken id-form mismatches that would be absorbed by this same
      marker-format migration — no separate follow-up todo is needed beyond the existing Deferred P2. **Verdict**: dated
      re-confirmation that the gate is still blocked; batch6 candidacy recorded.

- [x] ✅ [DOC] P2. **Author the missing gated finalize sibling for the bitfinex/bitget reclassified doc.** —
      unified-trading-pm@4d1335744
      `/plans/active/issues/execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md` was flipped
      `assigned_vm: NA` → `planning` in place by the 2026-07-30 na-eligibility-audit, but never received the paired
      `_finalize` sibling that both the naming SSOT's shape (b) and `task_template.md` § 4's finalize-plan-coverage rule
      require of an AO-dispatched doc — batch5 identified this gap and deliberately left it to this plan rather than
      inventing a doc mid-batch. Author `execution_service_bitfinex_bitget_native_unreachable_finalize_<today>.md`
      following shape (b): `depends_on: [execution_service_bitfinex_bitget_native_unreachable_2026_07_28]` +
      `gate_on_depends: true` + `sequential: true`, tagged `[ao-dispatch, close-out, reclassification, na-audit]`, whose
      todos reconcile that doc's factory.py wiring checkbox and run the 6-step archival ritual on it. **Check first
      whether another worker has since created it** — this is a known-shared corpus gap, a sibling audit may have closed
      it. **Done when**: the finalize sibling exists with a correct `depends_on` pair (or is confirmed already created
      by someone else), and `check_finalize_plan_coverage.py` no longer reports that doc as uncovered. Repo:
      unified-trading-pm.

- [ ] [DOC] P1. **Archive `cefi_satellite_ao_dispatch_batch5_2026_08_02.md`** via the standard 6-step ritual: migrate
      every remaining Deferred item to a tracked todo elsewhere (todo 2 above should have resolved or re-confirmed it —
      verify nothing silently vanishes) → add the archive banner → run the codex-alignment check (batch5 creates no new
      durable contract; confirm still true) → grep the corpus for every referrer of
      `cefi_satellite_ao_dispatch_batch5_2026_08_02` and repoint each to the archived path → clear `locked_by` (already
      empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_08/`, every corpus referrer resolves to
      the new path, `run_hygiene_sweep.sh` stays green, and this finalize doc is archived alongside it in the same
      commit.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual todo 4 executes.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 1 shape (b) — the reclassified-doc
  finalize-sibling convention todo 3 restores.
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3a — the reversibility bar todo 2 checks for before the
  deferred marker-format migration can move to a future batch.

## Progress Log

- **context-scout 2026-08-03**: re-confirmed context_scope (3 entries) unchanged — already matches this doc's own "Codex
  SSOTs" citations; `_finalize` gate doc, so no source-code paths added per the skip-source carve-out.
