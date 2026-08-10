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
last_updated: "2026-08-08"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: ui_developer
effort: max
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
      origin/live-defi-rollout`) before citing it — do not copy batch 1's own evidence line blind. The 2 source docs: `data_status_cell_grid_rearchitecture_2026_07_18.md`(todo 1 of 7 — do NOT touch todos 2-7, still correctly NA/operator-gated) and`artifact_pipeline_observability_2026_07_17.md`
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

- [x] ✅ [REVIEW] P1. **Re-check all 11 of batch 1's `## Deferred` items for resolution.** Batch 1 found zero
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

      **DONE 2026-08-08.** All 11 verdicts, dated, with evidence:

          **Operator-gated (1-5):**
          1. `data_status_catalogue_true_source_phase2` — **STILL-BLOCKED.** No ruling; prerequisite (prediction
          `/catalogue` 79-row `_dedupe_latest` collapse) still unresolved per its own 2026-08-07 na-eligibility-audit.
          2. `data_status_cell_grid_rearchitecture` todo 2 — **STILL-BLOCKED.** Batch 1's own measurement todo shipped
          (`deployment-api@8a36931`, real numbers now recorded), but the bound/stream/precompute design gate itself is
          still an unmade 3-way architecture choice — reaffirmed by an 2026-08-08 na-eligibility-audit round7 pass.
          3. `deployment_api_inventory_alert_gate_ondemand_only` — **STILL-BLOCKED.** No ruling on the `[HUMAN]`-tagged
          reuse-vs-narrow-path trade-off; unchanged since 2026-07-30 per 2026-08-06 na-eligibility-audit.
          4. `consolidator_throughput_backlog_monitor`'s 2 `[REVIEW]` deploy-gate closers — **STILL-BLOCKED.** No tracker
          doc for "end-of-cockpit-plans" exists to check against; both closers remain explicitly deferred by the dated
          2026-07-10 operator decision, unchanged per 2026-08-07 na-eligibility-audit.
          5. `cost_observability_deferred_followups` — **CLEARED (operator ruled 2026-08-07), with a nuance.** (a) AWS CUR
          historical backfill: RULED CLOSED as July-2026-onward, final — no further work, not a batch candidate. (b)
          Business-context/`asset_group` enrichment: RULED "proceed," but a same-day 2026-08-08 scoping pass (captured in
          `ui_satellite_ao_dispatch_batch2_2026_08_08.md`'s own Deferred section) found it does NOT clear the
          bounded-outcome bar as a single todo — 176 VM launcher scripts exist, only ~9 route through the one shared
          label-injection choke point (143 call `gcloud compute instances create` directly), plus key-name drift
          (`asset_group=` vs `asset-group=`) on the ones that do pass labels. Direct precedent: a near-identical
          143-launchers-bypass shape on a different concern was operator-ruled 2026-08-06 to NOT be one bounded todo.
          Recommend it piggyback on the infra-tranche's `lc_gcloud_create` migration
          (`vm_launcher_setup_script_freshness_gap_2026_07_31.md`) rather than fork a parallel ui-tranche effort — not a
          fresh batch-2 candidate on its own.

          **Time-gated (6-7):**
          6. `deployment_registry_firestore_p3_cutover` GO/NO-GO criterion 1 — **STILL-BLOCKED**, fresh 2026-08-08
          live measurement (Firestore REST, full pagination, cross-checked against `gcloud compute instances list
          --filter=status=RUNNING`): only 48 of 176 currently-RUNNING GCE instances have a matching Firestore
          `status=running` doc (27% coverage, same under-coverage direction as 2026-07-30). **New this pass**: 509 of the
          557 `status=running` Firestore docs are genuinely stale (median heartbeat age 102h, not a convergence lag) —
          root-caused to `SyncService.reap_stale_deployments()` operating on the GCS registry only, never Firestore (zero
          `firestore` references in `sync_service.py`). Not a new defect — the doc's own todo 2 already anticipates
          migrating the reaper to Firestore — but it corrects the 2026-07-30 note's "passive wait" framing: criterion 1
          cannot converge without that migration landing. Full writeup + evidence added to the source doc's own Progress
          Log (its own re-verification convention). HALT stays in force; no batch-2 candidate.
          7. `deployment_registry_firestore_p5_verify` — **STILL-BLOCKED**, unchanged — sequenced behind item 6 landing in
          prod, which has not happened.

          **Too-large-or-risky (8-9):**
          8. `artifact_pipeline_observability` — **CLEARED for a closer-read pass (not one bounded todo).** Phase 7's
          CPU-throttling investigation is RESOLVED (operator ruling 2026-08-07: `cpu-throttling: false` confirmed live,
          `/api/artifacts/images` verified returning full real data, symptom no longer reproducible). Churn has settled
          (11 open items, stable across audits through 2026-08-08, no new phases opened). Both preconditions batch 1's
          Deferred section named are now met. Recommend a dedicated standalone closer-read/scoping session (not a blind
          single-todo extraction) to identify batch-3 candidates from its remaining 11 items — out of this todo's own
          scope to perform.
          9. `data_status_tab_and_downloads_remediation` — **Closer read DONE this pass.** `locked_by`: `locked_since`
          (2026-06-16) equals `created` (2026-06-16) — same-day, a WEAKER staleness signal than the
          `deployment_ui_smoke_failures` precedent (where the lock predated creation by 2 months, proven impossible); the
          doc also has continuous genuine activity through 2026-08-07 (operator APPLY-GATE rulings). Inconclusive either
          way — not resolved by this pass, doesn't block anything since the doc has real open work regardless. **8 open
          items catalogued, verdicts**: 3 CLEARED as one bounded batch-2 candidate — Phase A "Venue filter — frontend" +
          Phase B "Collapse duplicate panels" + "Pagination visible-count selector" are all CODE-SHIPPED
          (deployment-ui@80c547d) and blocked ONLY on a stale citation (`deployment_ui_fleet_git_nav_entry_regression`,
          resolved+archived 2026-07-29 per 2026-08-03 na-eligibility-audit) — candidate: re-run `pw:L2` full suite,
          tick all 3 on a confirmed exit 0. 1 CLEARED — Phase F "Verify YAHOO_FINANCE/KALSHI out-of-scope
          correct-by-design" `[DATA]` P2, cleanly bounded (batch 1's own Deferred description already flagged this as
          plausible). 1 CLEARED — the `[CODE]` P3 `BucketNamingError` follow-up (features-calendar/ml-service SHARED
          pseudo-key + features-cross-instrument-service `asset_group=None`), cleanly bounded, single deployment-api
          area. 1 CLEARED but low-priority — Phase B "Rollup-difference clarity" `[UI]` P3 (small optional tooltip). 2
          STILL-BLOCKED — the sub-bucket phantom-row audit (`[DATA]` P2, explicitly gated on the v9 `--apply` migration
          landing first, per its own text) and the `[DATA]` P0 APPLY GATE sign-off for defi/sports (explicit operator
          HOLD, 2026-08-07 — Ikenna still working canonicalisation).

          **Needs-verification (10-11):**
          10. `consolidator_throughput_backlog_monitor` WS-3 seam-endpoint todo — **CLEARED, already closed.** An
          independent 2026-08-07 na-eligibility-audit pass found + flipped it: all 4 concrete sub-parts were already
          individually shipped (`deployment-api@1a505c16`/`@14650f9`, `deployment-ui@15832cd`/`@368ea8e6`); the umbrella
          checkbox was simply never flipped alongside its parts. Already reflected in the source doc — no batch-2
          candidate needed.
          11. `cost_observability_deferred_followups`'s 4 unscheduled P3 items — **CLEARED, already covered.** Combined into
          ONE sequential todo in `ui_satellite_ao_dispatch_batch2_2026_08_08.md` (`status: active`, operator-approved
          2026-08-08, already dispatched) — same conclusion this todo's own closer-read instruction asked for (combine
          vs. confirm independence), already reached independently. No fresh batch-2 candidate needed — it's already in
          flight.

          **Batch-2/3 candidate summary (new, not already covered by an active batch):**
          - `data_status_tab_and_downloads_remediation_2026_06_16.md`: (a) re-run deployment-ui `pw:L2` full suite, tick 3
          already-shipped Phase A/B checkboxes on green; (b) `[DATA]` verify YAHOO_FINANCE/KALSHI out-of-scope
          correctness; (c) `[CODE]` fix the 2 named `BucketNamingError` sites. All 3 touch disjoint files/areas from each
          other and from batch 1/2's existing todos.
          - `artifact_pipeline_observability_2026_07_17.md`: needs a dedicated closer-read/scoping session first (not itself
          a bounded todo) — its own preconditions (Phase 7 resolved, churn settled) are now met.

- [x] ✅ [REVIEW] P1. **Re-measure the ui tranche's orphan count.** Re-run the `/ag-closeout-audit ui` classification
      over the tranche's now-updated docs (12 tranche-primary candidates as of this run — re-derive the current count
      fresh, don't assume it's still 12) and report the new orphan count against the 2026-08-06 baseline of **9 orphaned
      of 12 tranche-primary docs**. The count should have dropped by roughly the number of items batch 1 fully closed
      within its 2 touched source docs (note: neither source doc will FULLY close from batch 1 alone —
      `data_status_cell_grid_rearchitecture` still has todos 2-7 open and NA-gated, `artifact_pipeline_observability`
      still has 10 open items — so expect the orphan COUNT to stay similar even though real progress was made; the right
      check is whether each doc's REMAINING open item set is fully accounted for in this finalize's Deferred re-check
      above, not whether the doc count dropped). Any doc that did not move should be named with why (operator-gated /
      time-gated / too-large is a legitimate answer; "still orphaned for no stated reason" is not). Also verify
      `check_ag_closeout_linkage.py` still reports the ui tranche's closeout family as discoverable (it was verified
      non-empty as of the 2026-07-30 gate-coverage fix). **Done when**: the new orphan count is reported with per-doc
      reasons for anything that did not move. Repo: unified-trading-pm.

      **DONE 2026-08-08.** Re-derived the candidate set fresh (frontmatter-block-aware parse, not a single-line grep) —
          **14 tranche-primary candidates, not 12**: the original 12 plus the 2 self-referential parked-findings issue docs
          this skill's own prior runs produced (`issues/ag_closeout_audit_ui_parked_2026_08_07.md`,
          `issues/ag_closeout_audit_ui_parked_2026_08_08.md`), both newly in scope. Ran a 14-agent Workflow (one per doc,
          each given the full covering-plan-set context: consolidated closeout + batch1 [done] + this finalize's own
          todo1/todo2 verdicts + batch2 [active, 1 open todo] + batch2_finalize) — full per-doc verdicts in the workflow
          journal, `wf_b6d552e7-f14`. Result: **8 orphaned of 14** (4 `orphaned_partial_coverage` + 4 `orphaned_never_touched`),
          down from the 2026-08-06 baseline of 9/12 — 1 fewer orphan on a 2-larger denominator, i.e. genuine net progress
          once the denominator growth is accounted for. Zero Orthogonality-check mistags (all 14 cleanly single-tagged `[ui]`).

          **What moved (1 of the original 9 baseline-orphaned docs cleared)**:
          - `data_status_tab_and_downloads_remediation_2026_06_16.md`: `orphaned_never_touched` → `archivable_after_planned_work`.
          This finalize plan's own todo 2 (done above) did the closer-read this doc needed and found 5 of its 8 open items
          cleanly bounded; this finalize's still-open todo 4 (archival ritual) explicitly commits to migrating those cleared
          items into a real batch-2/3 plan when it runs — so the doc's remaining work is now covered-by-commitment from an
          active, gate-satisfied plan, not untouched.

          **What did NOT move (8 of the 9 baseline-orphaned docs — named with why, per the "no unstated reason" bar)**:
          1. `artifact_pipeline_observability_2026_07_17.md` — **too-large.** `orphaned_never_touched` → `orphaned_partial_coverage`
          (batch1 shipped 2 of 12 items — its Phase-5 metadata-gap fix) but 10 items remain untouched; needs a dedicated
          closer-read/scoping session (flagged by todo 2 above) before any of them can become a batch todo, not extractable
          as-is.
          2. `consolidator_throughput_backlog_monitor_2026_07_09.md` — **operator-gated**, unchanged. Its 2 remaining `[REVIEW]`
          deploy-gate closers stay deferred behind an unnamed "end-of-cockpit-plans" milestone with no tracker doc — no
          ruling landed since 2026-08-06.
          3. `data_status_catalogue_true_source_phase2_2026_07_24.md` — **operator-gated (cross-tranche)**, unchanged. Still
          blocked on the prediction `/catalogue` `_dedupe_latest` collapse-bug ruling, per that tranche's own 2026-08-07
          na-eligibility-audit — a UI-tranche-external prerequisite.
          4. `data_status_cell_grid_rearchitecture_2026_07_18.md` — **operator-gated**, `orphaned_never_touched` →
          `orphaned_partial_coverage`. Todo 1 (profiling) shipped via batch1, but todo 2's 3-way bound/stream/precompute
          architecture choice remains unmade (reaffirmed by 4 separate na-eligibility-audit passes through 2026-08-08),
          gating todos 3-7 behind it.
          5. `deployment_registry_firestore_p3_cutover_2026_07_14.md` — **operator/data-gated**, unchanged in orphan status.
          This finalize's own todo 2 re-measured GO/NO-GO criterion 1 live (27% Firestore/GCE coverage) and root-caused
          a new dimension (`reap_stale_deployments()` is GCS-only, never Firestore-aware) — real diagnostic progress, but
          the HALT itself is still correctly in force; nothing fixes it yet.
          6. `deployment_registry_firestore_p5_verify_2026_07_14.md` — **time-gated**, unchanged. Sequenced behind #5 landing
          in prod, which has not happened.
          7. `issues/cost_observability_deferred_followups_2026_07_10.md` — **too-large (partial)**. `orphaned_never_touched` →
          `orphaned_partial_coverage`: batch2 (active, 1 open todo) now claims 4 of its 5 open items, but the
          business-context/asset_group-enrichment item (operator-ruled "proceed" 2026-08-07) was found NOT safely bounded
          as one AO todo (176 VM launcher scripts, only ~9 through the shared choke point) and remains genuinely unscoped —
          recommended to piggyback on the infra-tranche's `lc_gcloud_create` migration instead of a fresh ui todo.
          8. `issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md` — **operator-gated**, unchanged. Still no
          ruling on the reuse-existing-endpoint-vs-narrow-path trade-off.

          **The 2 new (non-orphaned) candidates**: both self-referential parked-findings docs from prior audit passes
          self-classify `archivable_after_planned_work` — `..._parked_2026_08_07.md`'s 2 retag candidates are actively
          tracked by the consolidated closeout's own open P2 todo #5; `..._parked_2026_08_08.md`'s content is either
          already-actioned or already claimed by the now-active batch2.

          **Linkage gate**: `python3 scripts/plan-hygiene/check_ag_closeout_linkage.py` — 3 total corpus orphans (2 defi, 1
          ao), baseline 49, **zero `ui`-tagged orphans** — the ui tranche's closeout family remains discoverable, confirming
          the 2026-07-30 gate-coverage fix still holds for this tranche.

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
- **2026-08-08 — Todo 2 (re-check all 11 Deferred items) done (slot 27).** All 11 given a dated CLEARED/STILL-BLOCKED
  verdict with evidence — see the todo's own completion note for the full per-item writeup. Net: **4 CLEARED outright**
  (items 5-partial/10/11 already resolved or already covered by an existing active batch — no new batch needed for
  those), **2 CLEARED for extraction** (item 8's doc is now unblocked for a closer-read session; item 9's closer read
  surfaced 5 of its 8 open items as cleanly bounded batch-2 candidates), **6 confirmed STILL-BLOCKED** with restated
  live blockers (items 1-4, 6, 7) so batch 2 doesn't have to re-derive them. Notable: item 6's fresh live re-measurement
  (Firestore REST + `gcloud compute instances list`) found a new dimension to the Firestore P3 cutover's GO/NO-GO
  criterion-1 failure — 509 stale `status=running` docs (median 102h old) traced to `reap_stale_deployments()` being
  GCS-only — written up in that doc's own Progress Log per its re-verification convention, not a new issue doc (the fix
  is already scoped inside that plan's own todo 2). New batch-2/3 candidates identified (not yet drafted as a plan — out
  of this todo's own scope): 3 bounded items from `data_status_tab_and_downloads_remediation_2026_06_16.md` (pw:L2
  re-run + 3-checkbox tick; Yahoo/Kalshi scope-verify; 2 BucketNamingError fixes), plus a recommendation that
  `artifact_pipeline_observability_2026_07_17.md` get a dedicated scoping session now that its 2 blocking preconditions
  have cleared. Next: todo 3 (re-measure orphan count) is now dispatchable.
- **2026-08-08 — Todo 3 (re-measure orphan count) done (slot 7).** 14-agent Workflow classification (candidate set
  re-derived fresh at 14, not the assumed 12 — 2 new self-referential parked-findings docs from prior audit runs are now
  in scope). Result: **8 orphaned of 14**, down from the 2026-08-06 baseline of 9/12 —
  `data_status_tab_and_downloads_remediation_2026_06_16.md` cleared to `archivable_after_planned_work` on the strength
  of todo 2's own closer-read + this plan's still-open archival todo committing to migrate its cleared items forward.
  The other 8 baseline-orphaned docs are unchanged in orphan status, each named with a legitimate reason (operator-gated
  x5, time-gated x1, too-large-for-one-todo x2 — full per-doc breakdown in todo 3's own completion note above).
  `check_ag_closeout_linkage.py`: 0 `ui`-tagged orphans (3 total corpus orphans, all defi/ao) — the ui tranche's
  closeout family stays discoverable. Next: todo 4 (archive batch 1) is now dispatchable — its own migration commitment
  for `data_status_tab_and_downloads_remediation`'s 5 cleared items is now load-bearing per this todo's finding, not
  optional.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
