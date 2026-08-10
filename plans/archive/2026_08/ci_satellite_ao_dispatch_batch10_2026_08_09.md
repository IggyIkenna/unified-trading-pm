---
doc_type: plan
title: CI satellite AO batch 10 — tenth AO-dispatch extraction for the ci tranche (observability_master group)
summary: >-
  Sibling of `ci_satellite_ao_dispatch_batch9_2026_08_09.md` — same round-9 combined RECLASSIFY + satellite-extraction
  pass over `issues/plan_reconciler_ci_late_findings_2026_08_06.md`, split into a separate batch doc because its one
  extracted item's source doc (`monitoring_control_plane_master_2026_06_10.md`) carries `parent_epic:
  observability_master` rather than `infrastructure_master` — the same parent_epic-grouping split precedent
  batch7/batch8 established. See batch 9's own Progress Log for the full disposition of the source finding doc's other
  13 items; not duplicated here.
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, ao-dispatch, close-out, batch-10, satellite-docs, plan-hygiene, dangling-refs, observability_master]
related:
  [
    /plans/active/issues/plan_reconciler_ci_late_findings_2026_08_06.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch10_finalize_2026_08_09.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/monitoring_control_plane_master_2026_06_10.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
effort: low
sequential: false
drift_direction: none
context_scope:
  [
    /plans/active/issues/plan_reconciler_ci_late_findings_2026_08_06.md,
    /plans/active/monitoring_control_plane_master_2026_06_10.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Round-9 combined RECLASSIFY + satellite-extraction sweep, run 2026-08-09, against the `ci`-tranche candidate list.
  This item's source finding (`issues/plan_reconciler_ci_late_findings_2026_08_06.md` P1 finding 1) carries
  `parent_epic: observability_master` on its target doc, distinct from the `infrastructure_master` group extracted into
  sibling batch 9 — split per the parent_epic-grouping rule.
---

# CI satellite AO batch 10 (observability_master group)

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** Sole todo done + its source-doc checkbox reconciled by
> `ci_satellite_ao_dispatch_batch10_finalize_2026_08_09.md`'s own sole todo (`unified-trading-pm@cb35394451`). Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s "archive immediately" HARD RULE and the
> `ci_satellite_ao_dispatch_batch9_2026_08_09.md` / `..._batch9_finalize_2026_08_09.md` precedent for this exact
> batch-N/finalize shape (archived together earlier the same day). The checkbox-flip commit shipped separately from this
> git-mv archival commit per that same codex doc's "never combine" rule (see
> `issues/archive_candidates_hook_vs_no_combine_flip_archival_rule_conflict_2026_08_09.md`) — the `archive_exempt: true`
> bridge used on the finalize doc's flip commit is dropped there as moot now that both docs are leaving `plans/active/`.
> Successor: none.

> **Why this is a separate doc from batch 9.** Both batches come out of the same 2026-08-09 round-9 pass over the same
> source finding doc. This item's own target doc frontmatter names a different `parent_epic` (`observability_master`,
> not `infrastructure_master`) — grouping extractable items by `parent_epic` means a separate batch+finalize pair per
> group, even when the total item count is small (mirrors `ci_satellite_ao_dispatch_batch7_2026_08_09.md` /
> `ci_satellite_ao_dispatch_batch8_2026_08_09.md`).

## Todos

- [x] ✅ 1. [DOC] P2. **Repoint 6 stale `plans/active/` refs in `monitoring_control_plane_master_2026_06_10.md` to their
      archived paths.** All 6 targets are confirmed archived as of 2026-08-09 — re-verify fresh before editing (a target
      may have moved again since):
  - `plans/active/ci_dashboard_deployment_ui_2026_06_10.md` →
    `plans/archive/2026_06/ci_dashboard_deployment_ui_2026_06_10.md`
  - `plans/active/fleet_git_health_orchestrator_2026_06_10.md` →
    `plans/archive/2026_06/fleet_git_health_orchestrator_2026_06_10.md`
  - `plans/active/ci_status_firestore_side_store_2026_06_10.md` →
    `plans/archive/2026_06/ci_status_firestore_side_store_2026_06_10.md`
  - `plans/active/cicd_contract_hardening_2026_06_01.md` → `plans/archive/2026_06/cicd_contract_hardening_2026_06_01.md`
  - `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` →
    `plans/archive/issues/plan_line_cap_remediation_2026_07_23.md`
  - `plans/active/issues/dashboard_promotion_drain_visibility_2026_06_11.md` →
    `plans/archive/issues/dashboard_promotion_drain_visibility_2026_06_11.md`

    Fix every occurrence in `plans/active/monitoring_control_plane_master_2026_06_10.md` (frontmatter `related:` list
    entries AND inline body prose references — grep for each basename to find every occurrence, do not assume the
    frontmatter list is exhaustive). **Done when**: none of the 6 basenames above appear anywhere in
    `plans/active/monitoring_control_plane_master_2026_06_10.md` prefixed with a `plans/active/` path (a bare basename
    mention with no path, e.g. inside prose describing what shipped, is fine and does not need editing), and PM's
    `check_reference_paths.py` gate for this file is clean. Flip the source finding's checkbox in
    `issues/plan_reconciler_ci_late_findings_2026_08_06.md` (P1, "`monitoring_control_plane_master_2026_06_10.md` — 6
    `plans/active/` refs …") with the commit cited.

  - Source: `issues/plan_reconciler_ci_late_findings_2026_08_06.md`, P1 finding 1.

    **Done, 2026-08-09 (slot 31).** Re-verified all 6 targets fresh (still at the stated archive paths, none moved
    again). Fixed 5 `related:` frontmatter entries + 1 inline body-prose reference (the line-cap-remediation split
    banner) in `monitoring_control_plane_master_2026_06_10.md` — all repointed to leading-slash archive paths (existing
    bare-`plans/active/`-no-leading-slash entries corrected to the `/plans/...` convention at the same time). Confirmed
    zero remaining `plans/active/` occurrences of the 6 basenames. `check_reference_paths.py` run corpus-wide: both
    format (63 < baseline 81) and existence (68 < baseline 86) checks pass with no new violations. Source finding's
    checkbox flipped in `issues/plan_reconciler_ci_late_findings_2026_08_06.md`. Evidence: unified-trading-pm (this
    commit).

## Codex SSOTs (read before executing this todo)

- `/codex/11-project-management/cross-reference-path-convention.md` — leading-slash, repo-root-relative reference
  convention this todo must follow.
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan's sibling satisfies.

## Progress Log

- **2026-08-09** — Authored during the round-9 combined RECLASSIFY + satellite-extraction sweep, `ci` tranche, as the
  `observability_master`-group sibling of `ci_satellite_ao_dispatch_batch9_2026_08_09.md`. Conflict-checked against
  every active `ci`/`observability_master` batch and `monitoring_control_plane_master_2026_06_10.md`'s own body: no
  overlap found.
- **2026-08-09 (slot 31)**: Todo 1 done — see its own flip for full evidence. Source finding checkbox in
  `issues/plan_reconciler_ci_late_findings_2026_08_06.md` also flipped in the same commit (the finalize doc's own todo
  would otherwise duplicate this; it will just cite the already-landed commit).
- **2026-08-09 (slot 12)**: Correction to the note above — "no archival step is scoped" was written before the same-day
  `ci_satellite_ao_dispatch_batch9_2026_08_09.md` precedent established that a batch/finalize pair DOES archive together
  once the finalize plan's own todo closes. `ci_satellite_ao_dispatch_batch10_finalize_2026_08_09.md` reconciled the
  source-doc checkbox (`unified-trading-pm@cb35394451`); this doc and its finalize twin now archive together in this
  follow-up commit, per the 6-step ritual in `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.
