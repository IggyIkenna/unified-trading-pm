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
status: complete
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ui, ao-dispatch, close-out, batch-2, satellite-docs, archival, plan-hygiene]
related:
  [
    /plans/archive/2026_08/ui_satellite_ao_dispatch_batch2_2026_08_08.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-10" # all 4 todos done, archived per plan-completion-and-archival-discipline.md
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
    /plans/archive/2026_08/ui_satellite_ao_dispatch_batch2_2026_08_08.md,
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

> **🟢 ARCHIVED 2026-08-10 — COMPLETE.** All 4 todos done. Todo 1 reconciled the source doc's 4 P3 checkboxes (already
> flipped by slot-33); todo 2 re-checked the 1 Deferred item (STILL-BLOCKED — no batch-3 drafted); todo 3 re-measured
> the ui orphan count (~10 of 16); todo 4 archived `ui_satellite_ao_dispatch_batch2_2026_08_08.md` via the standard
> 6-step ritual alongside this finalize doc, in the same commit set. Successor: none (batch-3 was not warranted).

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

- [x] ✅ [REVIEW] P2. **DONE 2026-08-10 (slot-9, review)** — **Re-check batch 2's 1 `## Deferred` item: STILL-BLOCKED.**
      `issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md`'s standing P3 follow-up todo ("dedicated migration
      plan for remaining ~136 raw-create launchers to `lc_gcloud_create`") is **still open** — no dedicated plan has
      been authored. Only 3 of ~139 launchers migrated to `lc_gcloud_create` (first batch, deployment-service@6998cc228,
      2026-08-08). Live recount 2026-08-10: `lc_gcloud_create` callers = 10, raw `gcloud compute instances create`
      callers = 149 — the gap has **widened**, not closed (new launchers added since the issue doc was filed, most
      bypassing the shared choke point). The 2026-08-09 incident (slot-28, documented in the issue doc's Progress Log)
      confirmed `lc_gcloud_create` still lacks `--provisioning-model=SPOT`/`--instance-termination-action` support,
      meaning SPOT-backfill launchers cannot migrate to it yet. With only ~6% (10/159) of launchers routing through the
      shared label-injection choke point, the precondition for the read-side half (critical mass of labeled resources
      making the work meaningful) is not met. **No future-satellite-batch candidate drafted** — the deferred item's
      recommendation from the batch-2 plan stands unchanged: this enrichment item should piggyback on the
      infra-tranche's `lc_gcloud_create` migration, not fork a parallel effort. A future ui-tranche audit should
      re-measure the infra migration's progress before re-assessing bounded-ness. **Evidence**: direct read of the issue
      doc's open follow-up todo + live `grep -c` counts on `deployment-service/scripts/vm/*.sh` confirming the migration
      is barely started. Repo: unified-trading-pm.

- [x] ✅ [REVIEW] P2. **DONE 2026-08-10 (slot-9, review)** — **Re-measured ui tranche orphan count: ~10 of 16.**
      Baseline was 9 of 13 (2026-08-08). Changes: **(a)** `cost_observability_deferred_followups_2026_07_10.md` moved
      `orphaned_never_touched` → `orphaned_partial_coverage` — batch2 shipped all 4 P3 items (all now `[x]` citing
      `deployment-api@6a536a82d` + `deployment-ui@b7beaf33b`), but the business-context enrichment item remains open and
      uncovered (STILL-BLOCKED, per todo 2 above). AWS CUR backfill already `[x]` (ruled CLOSED 2026-08-07). Net: 1 of 5
      formerly-open items still uncovered — partial, not resolved. **(b)** Denominator grew 13→16: 3 docs added since
      2026-08-08: `deployment_api_unauthenticated_prod_p0_2026_08_10.md` + finalize (self-covering,
      `assigned_vm:     planning`, active → NOT orphaned), `issues/plan_reconciler_findings_ui_2026_08_10.md`
      (`assigned_vm: NA`, 3 open todos, created today, not covered by any active batch plan → +1 orphan). **(c)** No
      previously-orphaned doc became non-orphaned; batch3 (2026-08-09) added coverage to
      `artifact_pipeline_observability` (already `orphaned_partial_coverage` via batch1) but didn't resolve it. **(d)**
      `check_ag_closeout_linkage.py`: 1 orphan found but it's `infrastructure` tranche, not ui — ui tranche closeout
      family is discoverable (0 ui orphans). **Caveat**: full Phase-1 per-doc re-read not run (REVIEW task, not full
      audit) — this is a delta analysis from the known 2026-08-08 classification, not a de-novo 16-doc
      re-classification. Repo: unified-trading-pm.

- [x] ✅ [DOCS] P2. **DONE 2026-08-10 (slot-16)** — **Archive batch 2 per the 6-step ritual, and only then.** All 6
      steps executed: (1) the still-open Deferred item (business-context-enrichment, STILL-BLOCKED per todo 2) migrated
      as a documented cross-reference on `ui_consolidated_closeout_2026_07_30.md`'s Track 3 close-out criterion (no
      batch-3 created — todo 2 found it not clearable); (2) archival banner added + `status: superseded` +
      `superseded_by: ui_satellite_ao_dispatch_batch2_finalize_2026_08_08`; (3) codex-alignment check run — updated
      `/codex/05-infrastructure/billing-cost-observability.md` to document the new contract fields the shipped todo
      established (`discount_rate_pct`, `cost_per_unit`/`usage_amount`/`usage_unit` on sku rows, month-aware AWS
      provisional cutoff, "Other resources" leaf); (4) confirmed no CLAUDE.md change needed (the codex doc is the SSOT);
      (5) repointed every active-corpus referrer's path to
      `/plans/archive/2026_08/ui_satellite_ao_dispatch_batch2_2026_08_08.md` (epic relative refs +
      `plan_reconciler_findings_ui` related frontmatter); (6) confirmed batch 2 has no `locked_by` (no-op). Then
      physically moved batch 2 under `plans/archive/2026_08/` via `git mv` (mode-1 combined flip+archival for this
      finalize, sanctioned per `plan-completion-and-archival-discipline.md`). **Done when verified**:
      `run_hygiene_sweep.sh --ci --no-regen` = 0 hard, `check_reference_paths.py` shows no NEW dangling ref above its
      baseline, `regenerate_active_plan_inventory.py` = 0 orphans. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/11-project-management/` (findings triage, archival ritual, issue-doc lifecycle) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` (`status: draft` semantics) ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08** — Drafted alongside `ui_satellite_ao_dispatch_batch2_2026_08_08.md` by `ag_closeout_auditor` (dispatch
  agt-a0f1b7, `/ag-closeout-audit ui`, Autonomous mode). Ships `active` per the no-double-gate rule; genuinely cannot
  dispatch early due to `gate_on_depends: true`.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **slot-9 (review) 2026-08-10** — Todo 2 (re-check deferred item): **STILL-BLOCKED**. Verified
  `vm_launcher_setup_script_freshness_gap_2026_07_31.md`'s P3 follow-up todo remains open — no dedicated migration plan
  exists. Live recount: `lc_gcloud_create` callers 10, raw-create callers 149 — gap widening, not closing.
  `lc_gcloud_create` still lacks SPOT support (confirmed 2026-08-09 incident). With ~6% launcher penetration through the
  shared label-injection choke point, the read-side half is not meaningfully scoped yet. No future-batch candidate
  drafted — recommendation stands: piggyback on infra-tranche's own `lc_gcloud_create` migration. Re-measure at the next
  ui-tranche audit.
- **slot-9 (review) 2026-08-10** — Todo 3 (re-measure orphan count): **~10 of 16 orphaned** (baseline 9 of 13).
  `cost_observability_deferred_followups` moved `never_touched` → `partial_coverage` (4 P3s shipped, 1 business-context
  item STILL-BLOCKED). Denominator grew +3 (P0 incident pair self-covering, plan_reconciler findings ui +1 orphan).
  `check_ag_closeout_linkage.py`: 1 infrastructure orphan, 0 ui orphans — ui closeout family discoverable. Delta
  analysis from known 2026-08-08 classification, not de-novo 16-doc re-read.
- **slot-16 (ui_developer) 2026-08-10 — ARCHIVED.** Todo 4 executed the full 6-step ritual on
  `ui_satellite_ao_dispatch_batch2_2026_08_08.md`: deferred item cross-referenced onto the closeout's Track 3 criterion;
  banner + `status: superseded` + `superseded_by: ui_satellite_ao_dispatch_batch2_finalize_2026_08_08`; codex-alignment
  update to `billing-cost-observability.md` (new `discount_rate_pct` / `cost_per_unit` / `usage_amount`/`usage_unit`
  fields + month-aware AWS provisional + "Other resources" leaf); no CLAUDE.md change needed; active-corpus referrers
  repointed to the archive path (epic relative refs + plan_reconciler related); no lock to clear. Batch 2 `git mv`'d to
  `plans/archive/2026_08/` + this finalize doc archived (mode-1 combined flip+archival). Hygiene sweep / ref-check /
  orphan-count all verified green.
