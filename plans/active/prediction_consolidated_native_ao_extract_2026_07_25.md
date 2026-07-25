---
doc_type: plan
title: Prediction consolidated closeout — native-todo AO extract (2026-07-25 fresh triage)
summary: >-
  First AO-eligibility triage of prediction_consolidated_closeout_2026_07_18.md's OWN native `- [ ]` todos (distinct
  from the prediction_satellite_ao_dispatch_batch1/2 docs, which extracted from OTHER orphaned prediction plans/issues
  and never touched this parent's own dispatch surface). Of the parent's 7 native open todos (1 in "Distinct Values /
  axis-value census", 6 in "Queued audits + reviews"), 5 are AO-eligible now — 2 fully (adapter dead-code audit,
  adversarial AO-dispatch-readiness pass), 3 as the currently-dispatchable PRE-Phase-B slice of a todo whose full scope
  also needs a not-yet-started Phase-B migration in flight (partial-parallelism SPLIT per task_template.md §4). One of
  those 3 (the /data-pipeline-reconciliation todo) turned out to need NO new live run at all — this triage found an
  already-existing, uncited `data_pipeline_reconciliation_prediction_2026_07_24.md` report that already serves as the
  2nd of 3 required dated passes; the candidate below is pure verify-and-cite. The remaining 2 native todos stay out of
  this batch: the P3 "duplicate note" is not independently actionable (fully subsumed by the reconciliation todo, same
  Phase-B-post-migration blocker), and the P1 POLYMARKET `prediction_trades` schema-extension todo stays human — its own
  linked issue doc states the trader-identity/PII field list "needs a separate call", an unresolved UAC canonical-schema
  architecture decision, not a bounded worker task.
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, native-extract, conflict-checked]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/prediction_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
    /plans/active/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Fresh AO-eligibility triage session 2026-07-25, dispatched specifically to check
  `prediction_consolidated_closeout_2026_07_18.md`'s own native todos (never previously triaged — batch1/batch2 both
  extracted from OTHER orphaned prediction docs by design). Method: task_template.md §4's dispatch-scope-eligibility bar
  (bounded/checkable outcome only, no judgment calls) + the same conflict-check discipline batch1/batch2 used against
  each other and against the parent doc.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Prediction consolidated closeout — native-todo AO extract

> **Status: draft.** Per CLAUDE.md's plan-destination rule, a triage-drafted AO batch is never auto-shipped to `active`
> — flip this frontmatter's `status` to `active` only after operator review.
>
> **`sequential: true` — why.** All 5 todos below write their Done-when evidence into
> `prediction_consolidated_closeout_2026_07_18.md`'s own Progress Log (the parent doc IS the source here, unlike
> batch1/2 where the source was a different sibling doc) — a same-file target for every item in this plan. Per
> `task_template.md` §4 ("tasks that share a file → `sequential: true`"), this plan is serialised end-to-end instead of
> combining 5 differently-tagged ([BACKEND]/[DATA]×3/[REVIEW]) items into one todo, which would have blurred per-task
> role routing for no benefit — sequencing already prevents the concurrent-write collision.
>
> **No GCS delete / `--apply` mutation and no VM launch appears in any todo below** — `task_template.md` finding O's
> delete/VM-launch tagging requirement does not apply to this batch.

## Todos

- [ ] [BACKEND] P2. **Adapter dead-code/fallback audit.** Audit instruments-service's and market-tick-data-service's
      prediction adapters for dead code, silent fallback branches, and duplicated logic, per
      `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. Exact paths:
      `instruments_service/reference_data/adapters/prediction/kalshi.py` + `.../adapters/prediction/polymarket/`
      (instruments-service), `.../adapters/prediction/` (market-tick-data-service). **Awareness note (not a done-when
      gate)**: `prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 1 already targets one known defect on this
      surface — the dead `trading-api.kalshi.com` host — but in a DIFFERENT file
      (`e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py`, not the adapter files themselves); if
      batch1 has landed by the time this runs, don't re-file that as a new finding, just note it's already tracked.
      Repos: instruments-service, market-tick-data-service (read + new-finding-doc writes only). **Done when**: every
      adapter file in scope has either a filed finding (a new `plans/active/issues/<slug>.md`, one per distinct defect
      class found) or an explicit "0 findings" line recorded in `prediction_consolidated_closeout_2026_07_18.md`'s
      Progress Log — not silence. On success, flip this todo's corresponding checkbox in that doc's "Queued audits +
      reviews" section (the [BACKEND] P2 adapter-audit item). Source: `prediction_consolidated_closeout_2026_07_18.md`,
      "Queued audits + reviews".
- [ ] [DATA] P2. **`data-pipeline-check-is` — pre-Phase-B baseline checkpoint (partial slice).** Run
      `/data-pipeline-check-is --asset-group prediction` ONE time now as the pre-Phase-B baseline checkpoint. Phase B
      (the canonicalisation migration) has NOT started — it stays gated on a shared cefi/tradfi-migration VM drain
      window per the parent doc's "Deferred work after 2026-07-18" section — so only the PRE-Phase-B leg of the source
      todo's "twice more" requirement (pre-Phase-B baseline + Phase-B mid-migration spot-check) is currently
      dispatchable; the mid-migration leg is genuinely blocked (there is no migration in flight to spot-check yet). This
      is a partial-parallelism SPLIT per `task_template.md` §4 — the mid-migration leg stays tracked by the ORIGINAL
      todo in the parent doc, unchanged. Repo: market-tick-data-service / instruments-service (via the skill, `-test-`
      buckets only). **Done when**: the run's report path + date is recorded in
      `prediction_consolidated_closeout_2026_07_18.md`'s Progress Log, explicitly labeled "pre-Phase-B baseline (1 of
      2)" — do NOT flip the parent doc's original `data-pipeline-check-is` checkbox (it remains open pending the
      mid-migration leg). Source: `prediction_consolidated_closeout_2026_07_18.md`, "Queued audits + reviews".
- [ ] [DATA] P2. **`data-pipeline-check-mtds` — pre-Phase-B baseline checkpoint (partial slice).** Same structure as the
      `-is` todo above: run `/data-pipeline-check-mtds --asset-group prediction` ONE time now as the pre-Phase-B
      baseline (the MTDS prediction `-test-` bucket isolation fix already shipped per the parent doc's Ground-truth
      verdict, so this is safe to run against `-test-` buckets only); the Phase-B mid-migration spot-check leg stays
      blocked, tracked by the original todo. Repo: market-tick-data-service (`-test-` buckets only). **Done when**: the
      run's report path + date is recorded in `prediction_consolidated_closeout_2026_07_18.md`'s Progress Log,
      explicitly labeled "pre-Phase-B baseline (1 of 2)" — do NOT flip the parent doc's original
      `data-pipeline-check-mtds` checkbox. Source: `prediction_consolidated_closeout_2026_07_18.md`, "Queued audits +
      reviews".
- [ ] [DATA] P2. **`/data-pipeline-reconciliation` — verify predating run + cite the already-existing uncited pass (no
      new live run needed).** (a) Search the corpus (`plans/audit/results/`, `plans/active/`, `plans/archive/`) for a
      `/data-pipeline-reconciliation prediction` report dated BEFORE 2026-07-20 (the confirmed baseline,
      `plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_20.md`); record found-with-path or
      confirmed-absent. (b) **This triage already found** a second, later dated pass that exists but is NOT yet cited
      anywhere in `prediction_consolidated_closeout_2026_07_18.md`:
      `plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_24.md` — it explicitly diffs against the
      2026-07-20 baseline (reachable_coverage 95.82% vs 94.63%; F2 malformed `instrument_type` 76 `prediction` rows,
      unchanged, + 70 blank, was 30). Cite this report as the 2nd of the 3 required dated passes in the parent doc's
      "Distinct Values / axis-value census" section (which currently cites only the 2026-07-20 run). With (a)'s result +
      this citation, either 2-of-3 or 3-of-3 dated runs already exist — **only the post-Phase-B-migration final-gate
      pass (genuinely blocked until Phase B lands) can remain**; do not run a NEW live reconciliation pass as part of
      this todo, the discovery IS the deliverable. Repo: unified-trading-pm (docs only, read + cite). **Done when**:
      (a)'s search result and (b)'s citation are both recorded in `prediction_consolidated_closeout_2026_07_18.md`'s
      Progress Log with the exact report path(s); the "Distinct Values / axis-value census" section is updated to list
      the 2026-07-24 pass alongside the 2026-07-20 baseline. **Note for the finalize plan**: this does NOT fully satisfy
      the parent doc's P3 "Duplicate note" todo (Distinct Values section) — that todo's own done-when explicitly
      requires POST-Phase-B-migration numbers, which neither the 07-20 nor 07-24 pass is. Source:
      `prediction_consolidated_closeout_2026_07_18.md`, "Queued audits + reviews" + "Distinct Values / axis-value
      census".
- [ ] [REVIEW] P2. **Adversarial AO-dispatch-readiness pass (Track-Y-style).** Run the same adversarial
      AO-dispatch-readiness pass sports's Track Y ran (method: the archived
      `sports_consolidated_closeout_history_2026_07_24.md`'s "Track Y — PLAN-QUALITY REMEDIATION" section, mirroring
      `task_template.md` §3 findings C/D/E/F/G/H) against `prediction_consolidated_closeout_2026_07_18.md` itself: check
      for bare `§X` shorthand, ambiguous verbs (absorb/incorporate/handle/address), delete-tagging inconsistency,
      missing definition-of-done, stale checkboxes (a todo already resolved elsewhere in the same doc but left `[ ]`),
      and unsafe digest-checkbox syntax (a "referenced, not duplicated" digest bullet using real `- [ ]` brackets
      instead of `- **[TAG]**`). Repo: unified-trading-pm (docs only). **Done when**: findings (or an explicit "0
      findings") are recorded in `prediction_consolidated_closeout_2026_07_18.md`'s Progress Log, mirroring Track Y's
      format; on success, flip this todo's corresponding checkbox in the parent doc's "Queued audits + reviews" section.
      Source: `prediction_consolidated_closeout_2026_07_18.md`, "Queued audits + reviews".

## Deferred — stays with the parent doc, not extracted (2 of the parent's 7 native todos)

- **P3 "Duplicate note" (Distinct Values / axis-value census section)** — not independently actionable: its own text
  says it's "satisfied automatically" once the reconciliation todo above is met, and its literal done-when requires
  POST-Phase-B-migration numbers, which this batch's todo 4 explicitly does not produce (Phase B hasn't started). Stays
  open in the parent doc, tracked there, re-check once Phase B lands.
- **P1 POLYMARKET `prediction_trades` schema-extension migration** — STAYS HUMAN. The parent doc frames this as a
  bounded "3-step sequence" (schema design → writer update + migration → register in the cutover inventories) against
  the linked issue doc
  (`plans/active/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`), but step 1
  (**Design the extended canonical `trades` schema**) is not actually bounded: the issue doc's own Q3 resolution states
  the trader-identity/PII fields (`proxy_wallet`/`name`/`pseudonym`/`bio`/`profile_image`) "need a separate call —
  privacy/PII-adjacent, confirm they're genuinely needed downstream before keeping them canonical" — an unresolved
  architecture + privacy judgment call on the UAC canonical schema (a cross-repo SSOT), not a checkable fact a worker
  can determine alone. Steps 2-3 (writer+migration, register) are gated on step 1 landing first (can't implement or
  register an undesigned schema) and step 2 additionally involves a prod-GCS copy+verify+delete — this entire item needs
  the operator's PII call before any of its 3 steps become AO-eligible, then a fresh conflict-check (step 2's delete
  needs `[OPERATOR]` + delete-safety-protocol citation once dispatchable). Left untouched in the parent doc.

## Conflict-check against existing satellite batches (2026-07-25)

Grepped `prediction_satellite_ao_dispatch_batch1_2026_07_25.md` and
`prediction_satellite_ao_dispatch_batch2_2026_07_25.md` for topical overlap with each candidate above:

- **Adapter dead-code audit**: no overlap — batch1 todo 1 fixes one already-KNOWN defect (dead Kalshi host) in a
  DIFFERENT file (`e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py`); this todo is a fresh systematic
  audit of the adapter files themselves for NEW findings, noted as an awareness caveat inline above, not a hard
  conflict.
- **`data-pipeline-check-is`/`-mtds` pre-Phase-B baselines**: no overlap — neither batch1 nor batch2 runs either skill;
  `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`'s P0 todo is the POST-migration final gate for both
  skills (temporally disjoint from a pre-Phase-B baseline, no race).
- **`/data-pipeline-reconciliation` verify+cite**: no overlap — batch2 todo 2 does a NARROWER, DIFFERENT check (a
  case-insensitive live read of just the `instrument_type` column in `availability_index.parquet`, writing to
  `prediction_phase_ab_residuals_2026_07_24.md`'s Progress Log) — not the same four-surface reconciliation skill, not
  the same target file.
- **Adversarial AO-dispatch-readiness pass**: no overlap — this is the first such pass against this parent doc; batch1
  and batch2 don't touch this defect taxonomy.

## Codex SSOTs

`/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md` (todo 1),
`/codex/02-data/reconciliation-finding-taxonomy.md` (todo 4, C2a/F2 vocabulary),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" (the bar applied
to every classification in this doc + the Deferred section above).
