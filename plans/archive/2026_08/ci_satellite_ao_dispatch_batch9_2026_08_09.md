---
doc_type: plan
title: CI satellite AO batch 9 — ninth AO-dispatch extraction for the ci tranche (infrastructure_master group)
summary: >-
  Round-9 combined RECLASSIFY + satellite-extraction sweep (2026-08-09) over
  `issues/plan_reconciler_ci_late_findings_2026_08_06.md` — a 14-item late-hunter findings doc where 8 items turned out
  to already be resolved (checkbox-vs-reality drift, fixed in place in the same pass) and 2 genuinely-still-open,
  bounded doc-hygiene items survive: repointing 4 stale cross-references and fixing one stale epic-index status line.
  Both extracted items carry `parent_epic: infrastructure_master`, matching this doc's own epic — a THIRD genuinely-open
  item from the same source doc (repointing 6 refs in `monitoring_control_plane_master_2026_06_10.md`) carries
  `parent_epic: observability_master` instead and is extracted separately into
  `ci_satellite_ao_dispatch_batch10_2026_08_09.md`, per the batch7/batch8 parent_epic-grouping precedent.
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, ao-dispatch, close-out, batch-9, satellite-docs, plan-hygiene, dangling-refs, infrastructure_master]
related:
  [
    /plans/active/issues/plan_reconciler_ci_late_findings_2026_08_06.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch9_finalize_2026_08_09.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch10_2026_08_09.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/epics/infrastructure_master.md,
    /plans/active/ci_satellite_ao_dispatch_batch8_2026_08_09.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: infra
effort: low
sequential: false
drift_direction: none
context_scope:
  [
    /plans/active/issues/plan_reconciler_ci_late_findings_2026_08_06.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/epics/infrastructure_master.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Round-9 combined RECLASSIFY + satellite-extraction sweep, run 2026-08-09, against the `ci`-tranche candidate list.
  Both todos below are re-verified-still-open items from `issues/plan_reconciler_ci_late_findings_2026_08_06.md` (P1
  finding 2 and P2 finding 1) — the other 6 findings in that P0/P1/P2 range were confirmed already resolved in the same
  pass (see that doc's own Progress Log), and are not duplicated here.
---

# CI satellite AO batch 9 (infrastructure_master group)

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** Both todos done + their source-doc checkboxes reconciled by
> `ci_satellite_ao_dispatch_batch9_finalize_2026_08_09.md`'s own sole todo (`unified-trading-pm@63b1044ea`). Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s "archive immediately" HARD RULE (and the
> `ci_satellite_ao_dispatch_batch7_finalize_2026_08_09.md` precedent for this exact batch-N/finalize shape), this doc
> and its now-done finalize companion archive together in this same follow-up commit — separate from the checkbox-flip
> commit per that same codex doc's "never combine the flip with the git mv" rule (see
> `issues/archive_candidates_hook_vs_no_combine_flip_archival_rule_conflict_2026_08_09.md` for the same-day rule
> interaction this tripped). Successor: none.

> **Why this is a separate doc from batch 10.** Both batches come out of the same 2026-08-09 round-9 pass over
> `issues/plan_reconciler_ci_late_findings_2026_08_06.md`. This doc's two items both cite a source doc whose own
> `parent_epic: infrastructure_master` matches this batch; batch 10's one item cites a source doc tagged
> `parent_epic: observability_master` instead — grouping extractable items by `parent_epic` means a separate batch+
> finalize pair per group, per the precedent `ci_satellite_ao_dispatch_batch7_2026_08_09.md` /
> `ci_satellite_ao_dispatch_batch8_2026_08_09.md` established.

## Same-file contention — read before editing this plan

Todos 1 and 2 touch disjoint files (`qg_host_adaptive_resource_governor_2026_07_14.md` vs.
`plans/epics/infrastructure_master.md`) — safe to run concurrently.

## Todos

- [x] 1. ✅ [DOC] P2. **Repoint 4 stale `plans/active/issues/` refs in
      `qg_host_adaptive_resource_governor_2026_07_14.md` to the archived path.** The target,
      `qg_host_governor_severe_contention_2026_07_13.md`, is archived at
      `plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md` (verify fresh with
      `find plans/active plans/archive -iname "qg_host_governor_severe_contention_2026_07_13.md"` before editing, in
      case it has moved again since 2026-08-09). Fix all 4 occurrences in
      `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` (as of this writing: the `related:` frontmatter
      list, the `source:` frontmatter list, one inline body reference in the "Codex SSOTs" section, and one inline body
      reference in the Phase-5 todos section) — grep-verify the exact current line numbers before editing rather than
      trusting these, since the doc may have been touched by another session since. **Done when**:
      `grep -n "plans/active/issues/qg_host_governor_severe_contention" plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`
      returns zero matches,
      `grep -c "plans/archive/issues/qg_host_governor_severe_contention" plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`
      returns 4 (or the then-current live count if it has drifted), and PM's `check_reference_paths.py` gate for this
      file is clean. Flip the source finding's checkbox in `issues/plan_reconciler_ci_late_findings_2026_08_06.md` (P1,
      "`qg_host_adaptive_resource_governor_2026_07_14.md` — 4 refs …") with the commit cited.
  - Source: `issues/plan_reconciler_ci_late_findings_2026_08_06.md`, P1 finding 2.
  - **Done** — all 4 occurrences (`related:`, `source:`, Codex-SSOTs inline ref, Phase-6 body ref) repointed to
    `/plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md` (leading-slash convention per
    `check_reference_paths.py`). Verified: stale-count grep = 0, archived-count grep = 4,
    `check_reference_paths.py --only` clean. Source finding flipped in
    `issues/plan_reconciler_ci_late_findings_2026_08_06.md`. — unified-trading-pm@a52672b6d (corrected 2026-08-09 by the
    batch9-finalize review pass — the SHA originally cited here, `89925f0c6`, does not resolve to a commit touching this
    file; `a52672b6d` is the actual shipping commit, matching this todo's content and verified an ancestor of
    `origin/live-defi-rollout`)

    **Independently confirmed, 2026-08-09 (slot 12):** reached the identical conclusion (same real commit,
    `a52672b6de60b62e98b5362c30155456f82e92f3` — `a52672b6d` and `a52672b6de` are both valid prefixes of it) via a
    separate content-match + ancestor-verify pass, before discovering this correction had already landed. See
    `plans/archive/issues/pm_qg_red_audit_batch10_finalize_2026_08_09.md` for the broader citation-drift finding (2
    other mis-cited SHAs corrected the same way, in `quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09.md`).

- [x] 2. ✅ [DOC] P2. **Fix the stale `status: active` for `mtds_retry_safe_default_audit_2026_07_14` in
      `plans/epics/infrastructure_master.md` (around L595-597, re-locate by grepping the slug fresh — the epic file
      churns).** The plan itself is archived at `plans/archive/2026_08/mtds_retry_safe_default_audit_2026_07_14.md` with
      `status: complete` in its own frontmatter — the epic's P3-backlog index entry is stale, same class of drift the
      epic previously fixed via a prior finding (cite the fix pattern used there, do not invent a new index-entry
      format). Update the epic-index line's status to `complete` (and confirm whether the epic's own archival/rollup
      convention wants the entry moved out of the "P3 — backlog; revisit quarterly" section entirely — follow whatever
      the epic's existing convention is for other already-complete entries in that section, don't guess a new one).
      **Done when**: `plans/epics/infrastructure_master.md`'s entry for `mtds_retry_safe_default_audit_2026_07_14`
      matches the plan's own real status, and `plans/epics/infrastructure_master.md` stays under its 2000-line hard cap
      (`check_line_caps.sh`). Flip the source finding's checkbox in
      `issues/plan_reconciler_ci_late_findings_2026_08_06.md` (P2, "`plans/epics/infrastructure_master.md:595-597`…")
      with the commit cited.
  - Source: `issues/plan_reconciler_ci_late_findings_2026_08_06.md`, P2 finding 1.
  - **Done** — line 597 updated to
    `status: complete (archived 2026-08-06 — 5/5 todos done; fleet-wide STEP 5.104 lint in base-service.sh is the durable pin)`,
    matching the sibling `cicd_mvp_ldr_to_main_pipeline_2026_06_30` entry's format (L536). Entry stays IN PLACE in the
    P3 section (that sibling convention keeps completed entries in their original section, doesn't relocate them).
    `plans/epics/infrastructure_master.md` at 780 lines, well under the 2000-line hard cap. Source finding flipped in
    `issues/plan_reconciler_ci_late_findings_2026_08_06.md`. — unified-trading-pm@930f7393e

## Codex SSOTs (read before executing any todo)

- `/codex/11-project-management/cross-reference-path-convention.md` — leading-slash, repo-root-relative reference
  convention both todos must follow.
- `/codex/11-project-management/doc-frontmatter-schema.md` — epic-index entry conventions.
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan's sibling satisfies.

## Progress Log

- **2026-08-09** — Authored during the round-9 combined RECLASSIFY + satellite-extraction sweep, `ci` tranche. Both
  todos are re-verified-still-open items from `issues/plan_reconciler_ci_late_findings_2026_08_06.md`; the doc's other 6
  P0/P1/P2 findings in the same priority range were confirmed already resolved in the same pass (checkboxes flipped in
  place, not duplicated here). Conflict-checked against every active `ci`/`infrastructure_master` batch (1, 4-8) and
  `qg_host_adaptive_resource_governor_2026_07_14.md`'s own body: no overlap found — neither target file is claimed by
  any other active batch todo.
- **2026-08-09 (batch9-finalize review pass)** — Verified both todos' cited commits resolve and are ancestors of
  `origin/live-defi-rollout` (`git merge-base --is-ancestor`). Todo 2's `930f7393e` checked out clean. Todo 1's cited
  `89925f0c6` does NOT resolve to any commit in this repo (it's a stray digit-transposition of an unrelated
  deployment-service commit) — located the actual shipping commit by content match (`a52672b6d`, "repoint 4 stale issue
  refs in qg_host_adaptive_resource_governor") and corrected the citation above. Both source-doc checkboxes in
  `issues/plan_reconciler_ci_late_findings_2026_08_06.md` now carry the verified SHAs.
- **2026-08-09 (archival)** — Flip commit (`unified-trading-pm@63b1044ea`) shipped separately from this archival move
  per the codex "never combine" rule. Archiving this doc + its finalize companion together now, in this follow-up
  commit: `status` → `complete`, `related:` repointed at the finalize doc's new archive path, referrers fixed
  corpus-wide (`ci_satellite_ao_dispatch_batch10_2026_08_09.md`, `issues/plan_reconciler_ci_late_findings_2026_08_06.md`
  `related:` entries). No codex-alignment change needed — both todos were pure reference/index-hygiene fixes already
  covered by `/codex/11-project-management/cross-reference-path-convention.md`.
