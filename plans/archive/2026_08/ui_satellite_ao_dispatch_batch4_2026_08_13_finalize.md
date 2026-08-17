---
doc_type: plan
title: ui satellite AO batch 4 — finalize
summary: >-
  Gated closeout for ui_satellite_ao_dispatch_batch4_2026_08_13.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source doc's checkbox
  (this was an extraction batch, so the source docs' own checkboxes are the ones that go stale), archives any source doc
  that reaches zero open todos as a result, and runs the standard 6-step archival ritual on the batch plan itself.
status: complete
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ui, ao-dispatch, satellite-batch, close-out, finalize]
related:
  [
    /plans/archive/2026_08/ui_satellite_ao_dispatch_batch4_2026_08_13.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: deployment_and_user_management_master
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
depends_on: [ui_satellite_ao_dispatch_batch4_2026_08_13]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/archive/2026_08/ui_satellite_ao_dispatch_batch4_2026_08_13.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-sweep session. Ships
  status: active (not draft) per the /ag-closeout-audit skill's 2026-07-30 finding: gate_on_depends already
  machine-holds every task until the batch's own todos are done, so a second draft-gate is redundant.
---

# ui satellite AO batch 4 — finalize

> **Machine-gated on `/plans/archive/2026_08/ui_satellite_ao_dispatch_batch4_2026_08_13.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`. **Correction (plan_reconciler
> agt-8fc5a6, 2026-08-16): the batch was operator-approved 2026-08-13 (`status: active`) and has since shipped all 11
> todos — the "stays `status: draft`" framing below described the moment this doc was authored, not current state.**
> This finalize plan itself needs no separate status flip either way (unchanged).

> **ARCHIVED 2026-08-17** — all 3 todos above complete: batch4's reconciliation evidence independently re-verified (all
> cited commit SHAs confirmed real ancestors of `origin/live-defi-rollout`), neither source doc reached zero open todos
> so no source-doc archival triggered, and the batch plan + this finalize plan both moved to `plans/archive/2026_08/` in
> this same turn. See `ui_satellite_ao_dispatch_batch4_2026_08_13.md`'s own archived banner for the corpus referrer-fixup
> detail.

## Todos

- [x] ✅ [REVIEW] P2. For every completed todo in `ui_satellite_ao_dispatch_batch4_2026_08_13.md`, reconcile the
      evidence back into its cited `Source:` doc's own checkbox. **Already reconciled by a prior session
      (`unified-trading-pm@5196dfcafc`, 2026-08-15) — verified fresh this turn, not just checkbox-trusted.** All 4
      distinct source docs cited across batch4's 11 todos independently confirmed reconciled:
      `data_status_tab_and_downloads_remediation_2026_06_16.md` (todos 1-4, all `[x]` with matching 2026-08-14/2026-08-15
      evidence — venue-filter/dup-panel/pagination `deployment-ui@d95f1934ef`, rollup-clarity `deployment-ui@8033b83651`,
      Yahoo/Kalshi correct-by-design, BucketNamingError `deployment-api@c1aab6e`/`@b014ae9`);
      `artifact_pipeline_observability_2026_07_17.md` (todos 6-9, all `[x]` — CloudBuildsTab port
      `deployment-ui@b3300a71a7`, dead-route retirement `deployment-api@3f13e4435e`, build→deploy latency join
      `deployment-api@764db37c33`, deploy-churn condition `deployment-api@ec80509550`);
      `plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md` (todo 5's actual edit target,
      batch3_finalize todo 1's cross-file conflict-check note — already added, `unified-trading-pm@e1c95fa82f`);
      `plans/archive/2026_08/issues/plan_reconciler_findings_2026_08_07.md` (todo 10, ACTIVE_INDEX.md fix — already
      `[x]`, `unified-trading-pm@e8bb0b8524`); and `plans/archive/2026_08/issues/plan_reconciler_findings_ui_2026_08_11.md`
      (todo 11, tranche-inventory script — already `[x]`, `unified-trading-pm@b2e3e5f8fe`). Every cited SHA
      independently re-verified via `git merge-base --is-ancestor <sha> origin/live-defi-rollout` this turn (all
      confirmed real ancestors, none fabricated/dangling). No un-reconciled item found.
- [x] ✅ [REVIEW] P2. For each source doc reconciled above, check whether it now has zero open todos. **Neither of the
      two live source docs reaches zero** — `data_status_tab_and_downloads_remediation_2026_06_16.md` still has open
      todos unrelated to batch4 (denominator-freshness trust annotation P3, DeFi sub-bucket phantom-row audit P2 gated on
      the defi/sports APPLY-GATE HOLD, and that APPLY-GATE sign-off itself P0); `artifact_pipeline_observability_2026_07_17.md`
      still has ~9 open todos (Phase 3d "What's running" tarball display P3, Phase 6 stretch fleet-wide SHA-pinning P3,
      the misattributed-VM-origin correction P3, the snapshot-worker P2, etc.). No archival triggered by this todo —
      both correctly stay in `plans/active/`.
- [x] ✅ [REVIEW] P2. `ui_satellite_ao_dispatch_batch4_2026_08_13.md` reached zero open todos (all 11 `[x]`, its own
      `## Deferred` states "None") — ran the standard 6-step archival ritual on it, then archived this finalize plan too,
      both to `plans/archive/2026_08/` in the same turn (single-repo/mode-1 combined flip+archival commit, sanctioned
      per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). Corpus-wide referrer sweep:
      `plans/epics/deployment_and_user_management_master.md`'s 2 relative-path links + status lines repointed to the
      archive path (the only real machine-followable referrer found); the other mentions
      (`ui_consolidated_closeout_2026_07_30.md`, `plans/active/issues/plan_reconciler_findings_all_2026_08_15.md`, and
      several already-archived docs) are bare-filename historical-record prose, not the leading-slash formatted
      convention — left as-is, matching the corpus precedent `plan_reconciler_findings_ui_2026_08_11.md`'s own
      2026-08-16 archival set for its 2 equivalent non-formatted mentions. No new codex contract established by this
      closeout — routine satellite-batch reconciliation, nothing to update in codex.
