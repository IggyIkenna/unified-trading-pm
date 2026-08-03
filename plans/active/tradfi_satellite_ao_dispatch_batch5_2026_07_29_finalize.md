---
doc_type: plan
title: TradFi satellite AO batch 5 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch5_2026_07_29.md — machine-held via depends_on plus
  gate_on_depends: true until all 15 of that plan's todos are done. Mirrors the batch1/batch2/batch3/batch4-finalize
  pattern: reconcile each distinct source doc's checkboxes once its batch-5 todo lands, then re-check batch5's own
  Deferred conflict-gated / too-large-or-risky / operator-gated items for any that have since cleared (in particular:
  has `tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`'s re-stamp fix shipped yet, clearing the
  multisource_backfill FX-drain conflict; did todo 2's re-measure clear the MDPS blocker, making
  tradfi_sp500_ml_and_arb_backtest_readiness a batch6 candidate), then archive batch5 via the standard 6-step ritual.
  **Corrected 2026-08-02**: this summary previously listed "has batch1's dry-run landed, making the legacy-twin-bucket
  delete ready for a direct operator ask" — that dry-run landed 2026-07-30 and measured twin coverage at **0%**, so the
  delete is NOT ready for an operator ask and that item is no longer a deferral to re-check but a corrected finding todo
  2 must act on (plus the unexplained 995 → 900 candidate-set shrink, now tracked there). **`status: active` since
  2026-07-30 (`233ebd614`)** — the old "stays draft until batch5 is approved" double-gate was removed corpus-wide
  because `gate_on_depends: true` + `depends_on` already machine-hold every todo here until batch5's last todo lands; a
  stacked `status: draft` only added a manual flip nothing automates.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-29"
last_updated: "2026-08-02"
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
depends_on: [tradfi_satellite_ao_dispatch_batch5_2026_07_29]
gate_on_depends: true
source: >-
  /ag-closeout-audit tradfi run 2026-07-29 (autonomous mode, scheduled daily `ag_closeout_auditor` worker), per
  task_template.md section 4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize
  plan, mirroring the tradfi batch1/batch2/batch3/batch4 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope: [/plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md, /plans/active/tradfi_consolidated_closeout_2026_07_18.md, /codex/12-agent-workflow/plan-completion-and-archival-discipline.md, /plans/PLAN_FORMAT.md, /cursor-configs/skills/ag-closeout-audit/SKILL.md]
---

# TradFi satellite AO batch 5 — finalize

> **Status: active** (frontmatter flipped 2026-07-30 by `233ebd614`, the corpus-wide removal of the redundant
> `status: draft` double-gate on finalize plans; body banner brought into line 2026-08-02 — it still read "Status:
> draft" and contradicted the frontmatter). Upstream `/plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`
> is likewise `status: active` (approved + dispatched 2026-07-30, `5a6bbefc3`). Being `active` does NOT mean this plan's
> todos are dispatchable yet — see the machine gate below, which is the only thing holding them.
>
> **Machine-gated on `tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`** (`depends_on` plus `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 15 tasks in that plan are `done`. `sequential: true` because
> todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 15 distinct source docs.** For each of
      `tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`'s now-done todos, flip or update the corresponding checkbox in
      its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-5 commit(s) that shipped
      it — verify the actual shipped commit exists before citing it. **Pay particular attention to todos 4/5/6** (the
      FX/YAHOO_FINANCE coordination cluster): confirm the coordination actually happened as instructed (one
      investigation cited by the other two, not three independent re-derivations) before flipping all three docs'
      checkboxes — if a worker duplicated the investigation instead of coordinating, note that as a process finding
      rather than silently accepting it. For every source doc: after reconciling, re-check whether it now has 0 open
      items (checkbox and prose). Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open items, and
      never touch a doc carrying a non-empty `locked_by`. **Done when**: all 15 source docs are reconciled with verified
      evidence, and any doc that genuinely reaches 0 open items is flipped to `status: resolved`.

- [ ] [REVIEW] P1. **Re-check batch5's own Deferred sections now that time has passed.** **First, two corrections landed
      2026-08-02 that this re-check must respect rather than re-derive** (see batch5's Deferred — conflict-gated
      section): (i) the legacy-twin bucket delete's premise was FALSE — twin coverage measures **0%, not 100%** (dry-run
      2026-07-30: 900 class-B twins loaded → 0 deletable, 900 blocked, all "canonical twin NOT captured in manifest"),
      and batch1's dry-run HAS landed, so the old "bring it to the operator for a go/no-go" recommendation is spent —
      **do not re-raise it as an operator ask**; the gate is technical, not a decision. (ii) **Investigate the
      unexplained 995 → 900 shrink in the legacy-twin candidate set** — the delete's candidate population is cited as
      995 class-B rows throughout `/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` (from the
      2026-07-10 full orphan sweep) but the 2026-07-30 dry-run loaded 900 from the same report URI, 95 fewer, with no
      explanation recorded anywhere in the corpus. Determine which of these is true and cite the evidence: the report
      was regenerated by a later sweep; 95 twins were folded/migrated/deleted by another pass; the loader silently drops
      malformed rows; or two report generations are being conflated. **Done when**: either the delta is explained with
      cited evidence and the stale 995 figure is corrected everywhere it appears in the signoff doc, or — if it cannot
      be resolved in this pass — it is filed as its own `plans/active/issues/` doc (a delete's candidate list mutating
      unexplained is a real data-correctness finding, not bookkeeping) and NOT closed as accepted. Then, for the 2
      conflict-gated items (`tradfi_multisource_backfill_2026_06_22.md`'s FX-yahoo-drain sequencing; the
      legacy-twin-bucket actual delete), the 4 too-large-or-risky items, and the operator-gated list: re-read the
      specific gating ground to check whether it has since cleared — if the operator has ruled, one side has shipped, or
      a dated section proves one claim stale, extract it as a new tracked todo in a follow-up `batch6` (do NOT draft it
      directly here); if still genuinely unresolved, leave it explicitly deferred and do NOT re-ask an already-asked
      operator question. **In particular**: check whether this batch's own todo 2 (MDPS re-measure) cleared the blocker
      gating `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` — if so, that doc becomes a strong,
      ready-to-triage batch6 candidate, flag it explicitly rather than leaving it in generic "too-large" language. Also
      verify the 2 process observations noted in batch5 (batch4-finalize still undispatched;
      registry_coverage_and_ao_readiness still draft) — if either has since been resolved, note it; if not, re-surface
      it once more (these are fresh observations from this pass, not a repeated ask). **Done when**: each
      Deferred/observation item has either (a) a note that it is ready for `batch6` extraction because its gate cleared,
      or (b) an explicit re-verified confirmation the gate is still open, with evidence cited.

- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved or re-confirmed all of them — verify none silently vanish) → add the archive banner →
      run the codex-alignment check (batch5 creates no new durable contract; confirm no drift) → grep the corpus for
      every referrer of `tradfi_satellite_ao_dispatch_batch5_2026_07_29` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself is archived
      alongside it in the same commit.

## Codex SSOTs

No new durable contract is created by this plan. `/codex/11-project-management/` carries the archival ritual;
`plans/PLAN_FORMAT.md` carries the `status: draft` and `gate_on_depends` semantics this plan relies on.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).

- **2026-08-02 (operator-ruled correction pass, doc-only)** — Todo 2 now carries two explicit, non-re-derivable
  instructions arising from a correction made to batch5's Deferred section the same day: (i) the legacy-twin bucket
  delete's premise was FALSE — twin coverage measures **0%, not 100%** (2026-07-30 dry-run: 900 loaded → 0 deletable,
  900 blocked) and batch1's dry-run has landed, so the old "go/no-go to the operator" recommendation is **spent**, not
  pending; (ii) the candidate set's unexplained **995 → 900** shrink is now tracked work with a stated done-when
  (explain with cited evidence, or file its own issue doc — never close as accepted). Also fixed this doc's own stale
  self-description: the body banner said "Status: draft" and the frontmatter `summary` said it "stays `status: draft`
  until batch5 is approved", both contradicting `status: active` — the 2026-07-30 flip (`233ebd614`, corpus-wide removal
  of the redundant finalize double-gate) changed frontmatter only and left the prose behind. No todo checkbox flipped;
  this plan's todos remain machine-gated on batch5's completion.
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
