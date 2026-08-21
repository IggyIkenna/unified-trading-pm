---
doc_type: plan
title: AO satellite AO batch 3 — bare /plans/ leading-slash reference sweep from the agent_operating_framework_master plan_reconciler pass
summary: >-
  Extracted from `plans/active/issues/plan_reconciler_findings_agent_operating_framework_master_2026_08_19.md` §3 —
  a `/plan-reconcile agent_operating_framework_master` pass found ~40+ remaining bare (missing-leading-slash)
  `plans/active/...`/`plans/archive/...` body citations across the epic's own 71-doc corpus (8 of the highest-visibility
  instances were already fixed inline during that pass; this batch covers the rest). Purely mechanical — add a leading
  slash to a citation string, no content/design judgment. The source doc's own §2 (3 REVIEW investigation items) and §4
  (`task_template.md` self-issue fixes, explicitly flagged for a deliberate human-attended edit given that file's
  fleet-wide authoring-SSOT blast radius) are NOT extracted here — left `assigned_vm: NA` in the source doc.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags:
  [
    ao,
    agent-orchestrator,
    ao-dispatch,
    close-out,
    batch-3,
    satellite-docs,
    satellite-extraction,
    na-eligibility-audit,
    plan-reconcile,
    cross-reference-convention,
  ]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch3_2026_08_21_finalize.md,
    /plans/active/issues/plan_reconciler_findings_agent_operating_framework_master_2026_08_19.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/task_template.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
effort: low
drift_direction: advance-docs
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/plan_reconciler_findings_agent_operating_framework_master_2026_08_19.md,
    scripts/plan-hygiene/check_reference_paths.py,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
source: >-
  `na-eligibility-audit 2026-08-21` (ao tranche, batch 3/3) — RECLASSIFY (per-todo split) of
  `plan_reconciler_findings_agent_operating_framework_master_2026_08_19.md` §3. Conflict-check run against every
  currently-active `assigned_vm: planning` doc and sibling `ao_satellite_ao_dispatch_batch*`/`infra_satellite_*`/
  `ci_satellite_*` docs — a broad grep for "bare...plans...ref"/"leading slash" matched only docs that mention the
  general convention in passing (e.g. consolidated-closeout hubs, `docs_reconcile_*` findings docs, other
  `plan_reconciler_findings_*` docs for OTHER tranches) — none is an active AO-dispatch todo covering this specific
  epic's own ~40-instance backlog. No overlapping claim found.
---

# AO satellite AO batch 3

> **`status: active`** — same convention as batch1-25. **`assigned_vm: planning` / `execution_scope: orchestrator-agent`**.

## Why this plan exists

`plan_reconciler_findings_agent_operating_framework_master_2026_08_19.md`'s § "Class-level finding: bare
(missing-leading-slash) `/plans/...` body citations" documents `check_reference_paths.py`'s own structural blind spot:
its `BARE_CODEX_RE` format check only validates bare `codex/...` refs, never `plans/...` ones — so this class (a real
violation of the CLAUDE.md HARD RULE that both `/codex/` and `/plans/` citations carry a leading slash) is invisible to
the mechanical gate and was only found by a manual `/plan-reconcile` hunter sweep. 8 of the highest-visibility instances
were fixed directly in that pass; the source doc's own text names the remaining concentration by file (with per-file
counts) rather than leaving it as an unbounded "sweep the corpus" ask — extracted here as a single bounded, mechanical,
per-file fix-up task so it actually gets dispatched instead of sitting as unexecuted prose in a `plan_reconciler`
findings doc.

**Explicitly excluded from this batch** (both stay `assigned_vm: NA` in the source doc):

1. **§2 "STILL-OPEN" (3 `[REVIEW]` items)** — recovering/closing a stalled prior `/plan-reconcile ao` run's missing
   hunter output, confirming whether a tradfi doc's 5 stale candidates were addressed, and confirming whether a
   named doc covers a repeated cross-cutting closeout recommendation. These are investigation-and-judge tasks
   (interpret whether evidence is sufficient to close vs. re-open), not pure mechanical fixes — left for a human/
   `/plan-reconcile` pass.
2. **§4 `task_template.md` self-issues (3 items: dedup a duplicate blockquote, fix 4 bare refs in the doc's own
   body, add a footnote once `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`'s still-open
   "zero-derived-parent-row" investigation closes)** — the source doc's own text explicitly flags these as
   deliberately NOT auto-fixed, given `task_template.md` is the fleet-wide plan-authoring SSOT every future
   plan-writing agent reads; that caution is respected here rather than overridden by a casual batch-extraction
   (same class of restraint already applied to `orchestrator_vm_e2e_hardening_2026_07_24.md`'s dirty-worktree
   dispatch-hook item). The footnote item is additionally blocked on a still-open sibling investigation.

## Todos

- [ ] [DOC] P3. **Fix the remaining bare (missing-leading-slash) `plans/...` body citations named in
      `plan_reconciler_findings_agent_operating_framework_master_2026_08_19.md` §3**, across these files (counts as
      measured by that pass; re-verify each file live before editing, since corpus drift since 2026-08-19 is expected):
      `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` (10),
      `safe_doc_push_orphaned_patch_describes_unshipped_ci_fix_2026_08_17.md` (remaining 2, after the pass's own
      partial fix of 2/4), `cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md` (1),
      `mdps_qg_tests_slice_oserror_cannot_send_recurrence2_2026_08_19.md` (3), plus any other `plans/active/*.md`/
      `plans/active/issues/*.md` body citation matching the pattern
      `[^/]plans/(active|archive)/[a-z0-9_/-]+\.md` (a bare citation, not already preceded by a leading slash) inside
      the `agent_operating_framework_master` epic's own corpus (the 71 docs the source `/plan-reconcile` pass
      enumerated: `plans/epics/agent_operating_framework_master.md`'s own `related_plans:`/body listing). Do NOT touch
      `task_template.md` (excluded above) or `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`
      /`operator_action_items_consolidated_2026_08_08.md` (the source doc names these as containing 8/12 instances
      already fixed in the original pass — re-verify they're clean before assuming so, but do not re-fix if already
      correct). **Done when**: a fresh `check_reference_paths.py --scope agent_operating_framework_master`-equivalent
      grep (`grep -rnE '[^/]plans/(active|archive)/[a-z0-9_/-]+\.md' <target files>`) finds 0 remaining bare-citation
      instances across the files named above, and every fixed citation still resolves to a real file (no dangling
      references introduced). Repo: unified-trading-pm.

## Progress Log

- **2026-08-21 (na-eligibility-audit, ao tranche batch 3/3)**: Authored as the per-todo-split extraction from
  `plan_reconciler_findings_agent_operating_framework_master_2026_08_19.md` §3. Conflict-checked against every
  currently-active `assigned_vm: planning` doc and sibling `*_satellite_ao_dispatch_batch*` docs — no overlapping
  claim found (a broad grep for "bare plans ref"/"leading slash" matched only docs discussing the general convention,
  not an active todo covering this specific epic's own remaining instances). No todos executed yet.
