---
doc_type: plan
title: Prediction consolidated closeout — native-todo AO extract finalize
summary: >-
  Gated closeout for prediction_consolidated_native_ao_extract_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 5 of that plan's todos are done. Unlike the batch1/batch2 finalize pattern (which
  reconciles checkboxes in a DIFFERENT sibling source doc), this extract's own source IS
  prediction_consolidated_closeout_2026_07_18.md — so this finalize plan reconciles checkboxes directly in the PARENT
  doc's "Queued audits + reviews" / "Distinct Values" sections, re-checks whether the 2 deferred native todos (P3
  duplicate-note, P1 POLYMARKET schema-extension) have newly cleared, and archives the EXTRACT batch doc itself (never
  the parent — the parent stays active with Phase B/C/D/E still open).
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, native-extract, archival]
related:
  [
    /plans/active/prediction_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_consolidated_native_ao_extract_2026_07_25]
gate_on_depends: true
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Prediction consolidated closeout — native-todo AO extract finalize

> **Machine-gated on `prediction_consolidated_native_ao_extract_2026_07_25.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 5 tasks in that plan are `done`.
> `sequential: true` because todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P2. **Reconcile the parent doc's checkboxes.** Of the extract batch's 5 todos, 2 are FULL completions
      (adapter dead-code audit, adversarial AO-dispatch-readiness pass) and 3 are PARTIAL (the `-is`/`-mtds` pre-Phase-B
      baseline runs, and the reconciliation verify+cite). In `prediction_consolidated_closeout_2026_07_18.md`'s "Queued
      audits + reviews" section: flip the 2 fully-completed todos' checkboxes to `[x]` with the evidence (filed-findings
      list or "0 findings" citation; Track-Y findings or "0 findings" citation). For the 3 partial todos, do NOT flip
      their checkboxes — instead append a dated Progress Log note recording exactly what landed (which leg of "twice
      more" / which dated pass) and what remains (the Phase-B mid-migration / post-migration leg), so a future reader
      doesn't re-investigate work already done. Also update the "Distinct Values / axis-value census" section per the
      extract batch's todo 4 (cite the 2026-07-24 reconciliation pass alongside the 2026-07-20 baseline, if not already
      landed by that todo's own execution). **Done when**: all 5 extract-batch todos have a corresponding, verified
      update in `prediction_consolidated_closeout_2026_07_18.md` (checkbox flip for the 2 full ones, Progress Log note
      for the 3 partial ones), citing the extract-batch's commit SHA(s) as evidence.
- [ ] [REVIEW] P2. **Re-check the 2 deferred native todos.** (a) P3 "Duplicate note": re-check whether Phase B (the
      canonicalisation migration) has landed since this extract was drafted — if yes, dispatch a new bounded todo
      (post-Phase-B `/data-pipeline-reconciliation prediction` run, diffed against the 2026-07-20 baseline) into a
      follow-up plan or directly if a live AO plan already exists for it; if Phase B still hasn't landed, leave it
      deferred with a dated re-check note. (b) P1 POLYMARKET `prediction_trades` schema-extension: re-check whether the
      operator has ruled on the trader-identity/PII field question (search
      `plans/active/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`'s Progress log and
      any `autonomous_session_operator_decisions_*.md` doc for a dated ruling); if ruled, the schema-design step becomes
      bounded — draft a new AO-eligible todo against the ruling's specific field list (plus `[OPERATOR]` +
      delete-safety-protocol citation for the migration step, per `task_template.md` finding O); if not yet ruled, leave
      it deferred. **Done when**: both (a) and (b) have an explicit current-state note (still gated / newly
      dispatchable, with a new todo/plan created if so).
- [ ] [DOC] P2. **Archive `prediction_consolidated_native_ao_extract_2026_07_25.md`** via the standard 6-step ritual
      (per CLAUDE.md's plan-archival rule): confirm the Deferred section above has nothing left unaddressed (todo 2
      should have already resolved what it could) → add the archive banner → run the codex-alignment check → grep the
      corpus for every referrer of `prediction_consolidated_native_ao_extract_2026_07_25` (including this finalize doc's
      own filename and `prediction_consolidated_closeout_2026_07_18.md` if a forward-pointer was added there) and fix
      each path to point at the archived location → clear `locked_by` (already empty here, confirm). **Do NOT** archive
      `prediction_consolidated_closeout_2026_07_18.md` itself — it stays `active` with Phase B/C/D/E still open; only
      the extract batch (and this finalize doc) move to `plans/archive/2026_07/`. **Done when**: the extract batch is
      moved to `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself
      gets archived alongside it in the same commit.

## Codex SSOTs

`/codex/11-project-management/` (plan archival ritual),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`.
