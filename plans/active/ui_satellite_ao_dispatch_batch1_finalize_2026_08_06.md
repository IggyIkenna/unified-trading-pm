---
doc_type: plan
title:
  UI satellite AO batch 1 — finalize (reconcile 2 source docs + re-check the 11 deferred items + re-measure orphan count
  + archive)
summary: >-
  Gated closeout for `ui_satellite_ao_dispatch_batch1_2026_08_06.md` — machine-held via `depends_on` + `gate_on_depends:
  true` until all 3 of that plan's todos are done, so this can never dispatch early. Batch 1 was extracted from 2 source
  docs (`data_status_cell_grid_rearchitecture_2026_07_18.md`, `artifact_pipeline_observability_2026_07_17.md`), so this
  finalize reconciles each of those 2 docs' corresponding checkboxes, then re-checks all 11 of batch 1's `## Deferred`
  items (a mix of operator-gated, time-gated, too-large-or-risky, and needs-verification — batch 1 found zero pure
  conflict-gated items, being the tranche's first batch with nothing yet to conflict with) to see which have since
  resolved and can become batch-2 candidates. Only then does the standard archival ritual run on batch 1. The goal is
  that after this plan, the ui tranche's real remaining work is either shipped, re-tracked as an explicit new todo, or
  confirmed still correctly gated — with the orphan count re-measured against this run's 9-of-12 baseline rather than
  assumed.
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ui, ao-dispatch, close-out, batch-1, satellite-docs, archival, plan-hygiene]
related:
  [
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: ui_developer
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [ui_satellite_ao_dispatch_batch1_2026_08_06]
gate_on_depends: true
sequential: true
source: >-
  `/ag-closeout-audit ui` run 2026-08-06 — mirrors the `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`
  gated-reconcile-then-archive pattern, per `plans/active/task_template.md` §4's finalize-plan-coverage rule (every AO
  batch plan needs a paired gated finalize).
---

# UI satellite AO batch 1 — finalize

> **`status: draft` in the parent batch does NOT apply here** — this finalize plan ships `active` from the start
> (`task_template.md`'s no-double-gate rule: `gate_on_depends: true` already machine-holds every task below until the
> batch's own 3 todos are `done`, so stacking a second manual `draft` gate on top would just be a redundant flip nobody
> reliably remembers). It genuinely cannot dispatch early regardless of its own `status`.

> **Machine-gated on `ui_satellite_ao_dispatch_batch1_2026_08_06.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 3 tasks in that plan are `done`. `sequential: true` because todo 2
> needs todo 1's reconciliation finished (to know which source docs still have real open work), and todo 4 (archival)
> must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile both source docs' checkboxes.** For each of batch 1's 3 now-done todos, find the
      corresponding checkbox in the source doc its text names (every todo ends with
      `Source: \`<doc>.md\``) and flip     it `[x]`, citing the batch-1 commit(s) that shipped it. **Verify each cited sha actually exists and is an     ancestor of `origin/live-defi-rollout`** (`git
      merge-base --is-ancestor <sha>
      origin/live-defi-rollout`) before     citing it — do not copy batch 1's own evidence line blind. The 2 source docs:     `data_status_cell_grid_rearchitecture_2026_07_18.md`(todo 1 of 7 — do NOT touch todos 2-7, still correctly     NA/operator-gated) and`artifact_pipeline_observability_2026_07_17.md`
      (2 of its Phase-5 items — do NOT touch its other 10 open items, still correctly deferred per batch 1's own
      reasoning). **Done when**: both source-doc boxes corresponding to done batch-1 todos are flipped with a verified
      sha, and either is left unflipped only with a stated reason. Repo: unified-trading-pm.

      **DONE 2026-08-08**: all 3 boxes across the 2 source docs were already `[x]` (flipped by the batch-1 todos
          themselves per their own "Done when" clauses), so this pass focused on sha-verification + citation completeness:
          (1) `data_status_cell_grid_rearchitecture_2026_07_18.md` todo 1 already cites `deployment-api@8a36931` —
          verified ancestor of `origin/live-defi-rollout`. (2) `artifact_pipeline_observability_2026_07_17.md` Phase 5's
          2nd item (dual-cloud-image-builds drift fix) already cites `unified-trading-pm@dab5f0273` — verified ancestor.
          (3) `artifact_pipeline_observability_2026_07_17.md` Phase 5's 1st item (line 652, stale issue-filing checkbox)
          was `[x]` but cited only "na-eligibility-audit", no batch-1 sha — root-caused: that checkbox was independently
          pre-flipped 2026-08-07 by a na-eligibility-audit pass (`unified-trading-pm@2b8073083`, verified ancestor) one
          day BEFORE batch-1's own todo 2 shipped (`unified-trading-pm@d2094b791`, verified ancestor) fixing the
          cross-referenced issue doc's stale `#1` item; added both shas as an explicit citation so the checkbox properly
          reflects both closures rather than crediting only the earlier one. All 3 shas verified via
          `git merge-base --is-ancestor <sha> origin/live-defi-rollout` before citing (none copied blind). — this plan's
          own reconciliation commit.

- [ ] [REVIEW] P1. **Re-check all 11 of batch 1's `## Deferred` items for resolution.** Batch 1 found zero
      conflict-gated items (the tranche's first batch has nothing yet to conflict with), so this step is broader than
      the conflict-only re-check other tranches' finalize plans run — check EVERY category: - **Operator-gated (items
      1-5)**: has the operator ruled on any of the 5 (prediction-catalogue dedupe design; cell-grid
      bound/stream/precompute design; the inventory alert-gate architecture choice; the "end-of-cockpit- plans"
      milestone for the Consolidators deploy gates; the cost-observability business-context/CUR-backfill calls)? A
      ruling converts the item to a normal batch-2 candidate. - **Time-gated (items 6-7)**: re-measure the Firestore P3
      cutover's GO/NO-GO criterion 1 (Firestore doc-count ≈ live-VM-count) with fresh live data — if it has now
      converged, item 6's remaining steps (still gated behind `[OPERATOR]` + delete-safety for the irreversible
      GCS-blob-delete steps specifically) become batch-2 candidates, and item 7 (P5 verify) can be re-evaluated once
      P3's cutover actually lands. - **Too-large-or-risky (items 8-9)**: has
      `artifact_pipeline_observability_2026_07_17.md`'s Phase 7 investigation (the operator-paused CPU-throttling
      hypothesis) resolved? Has its churn rate settled enough to reconsider a wider extraction? Has anyone given
      `data_status_tab_and_downloads_remediation_2026_06_16.md` the dedicated closer read item 9 recommends — in
      particular, is its `locked_by: live-defi-rollout` a genuine active claim or stale (see the Findings note below
      about the SAME field appearing on 62 corpus-wide docs)? - **Needs-verification (items 10-11)**: run the
      recommended `/plan-reconcile ui` check on item 10 (the Consolidators seam-endpoint todo, possibly already
      superseded by later-shipped work) — if confirmed done, flip its checkbox in the source doc directly rather than
      drafting a redundant todo. For item 11 (the 4 cost-observability P3 items), do the closer read batch 1 deferred:
      confirm which files each actually touches and either combine into 1-2 sequential todos or confirm genuine
      independence. For each item that clears, write an explicit batch-2 candidate line (source doc + the specific
      todo + the evidence). For each still-blocked one, restate the live blocker so batch 2 does not have to re-derive
      it. **Done when**: all 11 items carry a dated CLEARED-or-STILL-BLOCKED verdict with evidence, and the cleared set
      is written up as the batch-2 candidate list. Repo: unified-trading-pm.

- [ ] [REVIEW] P1. **Re-measure the ui tranche's orphan count.** Re-run the `/ag-closeout-audit ui` classification over
      the tranche's now-updated docs (12 tranche-primary candidates as of this run — re-derive the current count fresh,
      don't assume it's still 12) and report the new orphan count against the 2026-08-06 baseline of **9 orphaned of 12
      tranche-primary docs**. The count should have dropped by roughly the number of items batch 1 fully closed within
      its 2 touched source docs (note: neither source doc will FULLY close from batch 1 alone —
      `data_status_cell_grid_rearchitecture` still has todos 2-7 open and NA-gated, `artifact_pipeline_observability`
      still has 10 open items — so expect the orphan COUNT to stay similar even though real progress was made; the right
      check is whether each doc's REMAINING open item set is fully accounted for in this finalize's Deferred re-check
      above, not whether the doc count dropped). Any doc that did not move should be named with why (operator-gated /
      time-gated / too-large is a legitimate answer; "still orphaned for no stated reason" is not). Also verify
      `check_ag_closeout_linkage.py` still reports the ui tranche's closeout family as discoverable (it was verified
      non-empty as of the 2026-07-30 gate-coverage fix). **Done when**: the new orphan count is reported with per-doc
      reasons for anything that did not move. Repo: unified-trading-pm.

- [ ] [DOCS] P2. **Archive batch 1 per the 6-step ritual, and only then.** In order: (1) migrate every still-open
      Deferred item out of batch 1 into a real home — a batch-2 plan for anything that cleared in todo 2 above, and a
      named standalone-plan todo for `artifact_pipeline_observability` and `data_status_tab_and_downloads_remediation`
      if item 8/9's closer look confirms they still need dedicated treatment — **nothing may be lost to archival**; (2)
      add the archival banner + set `status: superseded` with `superseded_by:` pointing at the batch-2 plan if one was
      created; (3) run the codex-alignment check against the SSOTs batch 1 cites; (4) update CLAUDE.md / codex if any
      batch-1 todo established a new durable contract (unlikely for this small a batch, but confirm rather than assume);
      (5) **update every referrer's path corpus-wide** — grep for `ui_satellite_ao_dispatch_batch1_2026_08_06` and
      repoint each hit to the archived path, using leading-slash repo-root-relative form; (6) clear the lock (batch 1
      has none, so this is a no-op — confirm rather than assume). Then physically move it under
      `plans/archive/2026_08/`. Also fix the two stale-prose findings batch 1 surfaced while you're touching this
      tranche's docs: trim `ui_consolidated_closeout_2026_07_30.md`'s Track 3/Track 4 close-out-criterion prose (both
      still describe already-resolved sub-items — alerts N+1, mock/live parity — as open). **Done when**:
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard, `check_reference_paths.py` shows no
      NEW dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0 orphans. Repo:
      unified-trading-pm.

## Why this finalize plan looks different from the infra one

Infra's batch 1 finalize re-checked 10 purely CONFLICT-GATED deferrals (the one category that clears without a human
ruling) because infra's mature, 25-todo batch had already worked through everything else. This ui batch is the tranche's
FIRST-ever pass, 8 days after tranche launch, so its Deferred population is dominated by genuinely-new operator
questions and time-gates rather than resolvable cross-plan conflicts — todo 2 above is deliberately broader (re-check
every category, not just conflicts) to match that.

## Codex SSOTs

`/codex/11-project-management/` (findings triage, archival ritual, issue-doc lifecycle) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` (`status: draft` semantics) ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-06** — Drafted alongside `ui_satellite_ao_dispatch_batch1_2026_08_06.md` by `ag_closeout_auditor` (dispatch
  agt-8d6508, `/ag-closeout-audit ui`, Autonomous mode). Ships `active` per the no-double-gate rule; genuinely cannot
  dispatch early due to `gate_on_depends: true`.
- **context-scout 2026-08-07**: re-verified context_scope (6 entries, unchanged) — `*_finalize` gate doc, genuinely
  code-free (all 4 todos are checkbox-reconciliation/deferred-re-check/orphan-remeasure/archival, no code target); the
  existing list already matches this doc's own "Codex SSOTs" section plus the gated parent batch. No prior marker
  existed despite `context_scope` already being populated at doc-creation time — this is the first context-scout pass on
  this doc.
- **2026-08-08 — Todo 1 (reconcile source-doc checkboxes) done.** All 3 batch-1 todos had already flipped their own
  source-doc checkbox as part of shipping; this pass sha-verified all 3 citations against `origin/live-defi-rollout` and
  found + fixed one gap — the `artifact_pipeline_observability_2026_07_17.md` line-652 checkbox was flipped by an
  earlier, independent na-eligibility-audit commit (`unified-trading-pm@2b8073083`, 2026-08-07) rather than by batch-1's
  own todo 2 commit (`unified-trading-pm@d2094b791`, 2026-08-08), so it was missing the batch-1 citation — added both
  shas. `data_status_cell_grid_rearchitecture_2026_07_18.md` todo 1 (`deployment-api@8a36931`) and
  `artifact_pipeline_observability_2026_07_17.md`'s dual-cloud-drift item (`unified-trading-pm@dab5f0273`) were already
  correctly cited. Next: todo 2 (re-check the 11 Deferred items) is now dispatchable.
