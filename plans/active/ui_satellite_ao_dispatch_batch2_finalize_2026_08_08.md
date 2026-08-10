---
doc_type: plan
title:
  UI satellite AO batch 2 — finalize (reconcile 1 source doc + re-check the 1 deferred item + re-measure orphan count +
  archive)
summary: >-
  Gated closeout for `ui_satellite_ao_dispatch_batch2_2026_08_08.md` — machine-held via `depends_on` + `gate_on_depends:
  true` until that plan's 1 todo is done, so this can never dispatch early. Batch 2 was extracted from 1 source doc
  (`cost_observability_deferred_followups_2026_07_10.md`), so this finalize reconciles that doc's 4 corresponding
  checkboxes, then re-checks batch 2's 1 `## Deferred` item (the business-context-enrichment scoping question) to see
  whether the infra-tranche launcher migration it depends on has progressed enough to reconsider. Only then does the
  standard archival ritual run on batch 2.
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ui, ao-dispatch, close-out, batch-2, satellite-docs, archival, plan-hygiene]
related:
  [
    /plans/active/ui_satellite_ao_dispatch_batch2_2026_08_08.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: ui_developer
effort: max
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/ui_satellite_ao_dispatch_batch2_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [ui_satellite_ao_dispatch_batch2_2026_08_08]
gate_on_depends: true
sequential: true
source: >-
  `/ag-closeout-audit ui` run 2026-08-08 — mirrors `ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md`'s
  gated-reconcile-then-archive pattern, per `plans/active/task_template.md` §4's finalize-plan-coverage rule (every AO
  batch plan needs a paired gated finalize).
---

# UI satellite AO batch 2 — finalize

> **`status: draft` in the parent batch does NOT apply here** — this finalize plan ships `active` from the start
> (`task_template.md`'s no-double-gate rule: `gate_on_depends: true` already machine-holds every task below until the
> batch's own todo is `done`). It genuinely cannot dispatch early regardless of its own `status`.

> **Machine-gated on `ui_satellite_ao_dispatch_batch2_2026_08_08.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until that plan's 1 task is `done`. `sequential: true` because todo 2 needs
> todo 1's reconciliation finished, and todo 4 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile the source doc's 4 checkboxes — DONE 2026-08-10 (slot-33).** All 4 P3 checkboxes in
      `cost_observability_deferred_followups_2026_07_10.md`'s "## Unscheduled P3 enhancements" section were already
      flipped `[x]` citing the batch-2 SHAs: (1) month-aware AWS cutoff → `deployment-api@6a536a82d`; (2)
      credits/discounts view → `deployment-api@6a536a82d` + `deployment-ui@b7beaf33b`; (3) usage-quantity unit economics
      → `deployment-api@6a536a82d` + `deployment-ui@b7beaf33b`; (4) "Other resources" leaf table →
      `deployment-ui@b7beaf33b`. Both SHAs verified ancestors of `origin/live-defi-rollout`
      (`git merge-base     --is-ancestor`). All 4 sub-items shipped; none left open. Repo: unified-trading-pm.
      **Evidence**: verified 2026-08-10 — `deployment-api@6a536a82d` and `deployment-ui@b7beaf33b` both confirmed on
      origin.

- [ ] [REVIEW] P2. **Re-check batch 2's 1 `## Deferred` item for resolution.** Has
      `issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md`'s standing follow-up todo ("dedicated migration plan
      for remaining ~136 raw-create launchers to `lc_gcloud_create`") progressed enough that a critical mass of
      launchers now route through the shared choke point? If so, re-scope the business-context-enrichment item's
      READ-SIDE half (AWS cost-allocation-tag support in `cost_observability/models.py`, a `strategy` key in
      `BUSINESS_LABEL_KEYS`, a backfill script reconciling the `asset_group=`/`asset-group=` key-name drift already
      found in launchers that HAVE labels) as a possible future-satellite-batch candidate — this half is genuinely
      ui/cost-observability scoped and doesn't depend on the launcher-migration completing 100%, only on there being
      enough labeled resources to make the read-side work meaningful. Do NOT re-scope or draft the launcher-migration
      half itself — that stays infra-tranche's own surface regardless of progress. **Done when**: a dated
      CLEARED-or-STILL-BLOCKED verdict is recorded with evidence (the infra doc's own current todo/progress state), and
      if cleared, the read-side half is written up as an explicit future-satellite-batch candidate line (name corrected
      2026-08-10, plan_reconciler: "batch-3" is now taken by `ui_satellite_ao_dispatch_batch3_2026_08_09.md`, an
      unrelated artifact_pipeline_observability meta-items batch — use the next free number at execution time). Repo:
      unified-trading-pm.

- [ ] [REVIEW] P2. **Re-measure the ui tranche's orphan count.** Re-run the `/ag-closeout-audit ui` classification over
      the tranche's now-updated docs and report the new orphan count against this run's 9-of-13 baseline. Expect
      `cost_observability_deferred_followups_2026_07_10.md` to move toward
      `archivable_now`/`archivable_after_planned_work` only once ALL its remaining items (the 4 P3s this batch ships,
      plus whatever the business-context item's eventual disposition is) are accounted for — a partial ship (e.g. only 2
      of 4 P3 sub-items) should keep it `orphaned_partial_coverage`, not flip it prematurely. Also verify
      `check_ag_closeout_linkage.py` still reports the ui tranche's closeout family as discoverable. **Done when**: the
      new orphan count is reported with per-doc reasons for anything that did not move. Repo: unified-trading-pm.

- [ ] [DOCS] P2. **Archive batch 2 per the 6-step ritual, and only then.** In order: (1) migrate the still-open Deferred
      item out of batch 2 into a real home — a batch-3 plan if todo 2 above found it clearable, otherwise leave it as a
      documented cross-reference on `ui_consolidated_closeout_2026_07_30.md`'s own retag/follow-up todo rather than
      losing it; (2) add the archival banner + set `status: superseded` with `superseded_by:` pointing at batch-3 if one
      was created; (3) run the codex-alignment check against `/codex/05-infrastructure/billing-cost-observability.md`;
      (4) update CLAUDE.md/codex if the shipped todo established a new durable contract (unlikely for a 4-item
      UI/backend feature bundle, but confirm rather than assume); (5) update every referrer's path corpus-wide — grep
      for `ui_satellite_ao_dispatch_batch2_2026_08_08` and repoint each hit to the archived path, leading-slash
      repo-root-relative form; (6) clear the lock (batch 2 has none, so this is a no-op — confirm rather than assume).
      Then physically move it under `plans/archive/2026_08/`. **Done when**:
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard, `check_reference_paths.py` shows no
      NEW dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0 orphans. Repo:
      unified-trading-pm.

## Codex SSOTs

`/codex/11-project-management/` (findings triage, archival ritual, issue-doc lifecycle) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` (`status: draft` semantics) ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08** — Drafted alongside `ui_satellite_ao_dispatch_batch2_2026_08_08.md` by `ag_closeout_auditor` (dispatch
  agt-a0f1b7, `/ag-closeout-audit ui`, Autonomous mode). Ships `active` per the no-double-gate rule; genuinely cannot
  dispatch early due to `gate_on_depends: true`.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
