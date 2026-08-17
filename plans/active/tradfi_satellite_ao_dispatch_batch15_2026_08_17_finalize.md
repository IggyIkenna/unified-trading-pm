---
doc_type: plan
title: tradfi satellite AO batch 15 — finalize
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch15_2026_08_17.md — machine-held via depends_on +
  gate_on_depends until every todo in that batch is done. Reconciles each completed todo's evidence back into its
  TRUE source doc's checkbox (this was an extraction batch, so the source docs' own checkboxes are the ones that go
  stale), archives any source doc that reaches zero open todos as a result, and runs the standard 6-step archival
  ritual on the batch plan itself.
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-batch, close-out, finalize, na-eligibility-audit]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch15_2026_08_17.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_satellite_ao_dispatch_batch15_2026_08_17]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch15_2026_08_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source:
---

# tradfi satellite AO batch 15 — finalize

> Machine-held (`depends_on` + `gate_on_depends: true`) until every todo in
> `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` is done.

## Todos

- [ ] [REVIEW] P1. **Reconcile each completed batch-15 todo's evidence back into its TRUE source doc's checkbox.**
      For Todo 1 (source: `data_completion_tradfi_2026_07_15.md` item 15) — flip that item to `[x]` with evidence.
      For Todo 2 (sources: `dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_..._2026_08_16.md` item 2 AND
      `dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_..._2026_08_15.md` item 2) — flip BOTH source items to `[x]` citing
      this batch's evidence (they were consolidated into one batch todo; both source checkboxes need closing). For
      Todo 3 (source: the billing-rootcause doc item 2) — flip to `[x]`. For Todo 4 (source: the g01-6a-6l-2021
      stall doc item 2) — flip to `[x]`, and if Todo 4 resolved to "billing-caused, no code fix" rather than a code
      fix, make sure the source doc's evidence line says so explicitly (don't let a null-result read as
      not-done). For Todo 5 (source: the catalogue-scheduler doc, item at L120) — flip to `[x]` with the dry-run
      count + the confirmed-RUNNING scheduler-state evidence. For Todo 6 (archival) — no source-doc checkbox to
      flip (the archival IS the action); instead verify `tradfi_canonical_path_migration_design_2026_07_19.md` is
      actually gone from `plans/active/issues/` and present under `plans/archive/2026_08/issues/` with a banner. For
      Todos 7 and 8 — flip the corresponding items in `plan_reconciler_findings_tradfi_2026_08_16.md` (items 3 and
      4) to `[x]` with evidence; re-check whether item 4's original 7-doc count is now fully closed (3 done
      2026-08-16 + 4 done here = 7/7) and note that in the checkbox. Do NOT trust a source doc's own copy of the
      evidence line without re-verifying the cited commit/SHA actually exists.

- [ ] [REVIEW] P2. **Re-check any deferred/excluded-at-authoring-time follow-up** — specifically: did Todo 6's
      referrer sweep surface any NEW dangling reference that wasn't in the original ~43 count (a doc created between
      2026-08-17 and this finalize's run)? If so, spin it into a new tracked todo/plan rather than silently leaving
      it. Also check whether `plan_reconciler_findings_tradfi_2026_08_16.md`'s own items 2 and 5 (which stayed
      `assigned_vm: NA` per the 2026-08-17 audit's verdict — item 2 is line-cap-blocked pending an operator
      doc-split decision on `uac_data_type_validity_combinator_fragmentation_2026_07_07.md`, item 5 is gated by the
      na-eligibility-audit skill's own codex-edit carve-out) have had their gates clear since — if so, spin the
      newly-unblocked item into a fresh tracked todo rather than leaving it silently stale.

- [ ] [REVIEW] P3. **Check each source doc touched by Todo (1) above for zero-remaining-open-todos** — if
      reconciling a source doc's checkbox(es) left it with 0 open todos, that source doc is now ALSO an archival
      candidate and needs the standard 6-step ritual too, not just its own checkbox flip. Check specifically:
      `dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_..._2026_08_16.md`,
      `dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_..._2026_08_15.md`, the billing-rootcause doc, and the
      g01-6a-6l-2021 stall doc — each had exactly 1 other open item (an `[OPERATOR]` relaunch-decision todo) besides
      the one extracted here, so archival is NOT expected yet unless that operator item has since resolved too;
      verify rather than assume.

- [ ] [DOC] P1. **Run the standard 6-step archival ritual on this batch plan itself** (`tradfi_satellite_ao_dispatch_batch15_2026_08_17.md`
      + this finalize doc), including the corpus-wide referrer-path fixup, once all of the above is confirmed
      complete.

## Progress Log

- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): drafted alongside the batch, gated on
  its completion per the AO-dispatched finalize-plan-coverage rule.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
