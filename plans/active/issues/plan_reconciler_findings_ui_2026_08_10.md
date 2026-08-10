---
doc_type: issue
title: "plan_reconciler findings — ui tranche, 2026-08-10 (dispatch agt-ec1688)"
summary: >-
  Second sharded plan_reconciler run over the `ui` asset_group tranche (23 docs: 11 plans + 12 issues, incl. 3 batch
  docs + 3 finalize docs). Re-checks every item filed by the 2026-08-07 run (agt-a40e5f) plus fresh multi-agent fan-out
  coverage. In progress.
status: open
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, findings, ui, 2026-08-10]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/issues/plan_reconciler_findings_2026_08_07.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /plans/active/ui_satellite_ao_dispatch_batch2_2026_08_08.md,
    /plans/active/ui_satellite_ao_dispatch_batch3_2026_08_09.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: ui_developer
drift_direction: none
locked_by:
locked_since:
resolved_by:
source: "plan_reconciler dispatch agt-ec1688 — sharded ui tranche run 2026-08-10"
depends_on: []
---

# plan_reconciler findings — ui tranche, 2026-08-10

> **Run**: dispatch `agt-ec1688`, sharded to `tranche=ui`. 23 docs in scope (11 plans + 12 issues, incl. 3
> satellite-dispatch batches + 3 finalize docs). This is the SECOND `/plan-reconcile ui` run — the first (`agt-a40e5f`,
> 2026-08-07) applied zero fixes (grace/lock blocked everything) and is linked above.

## Coverage (hunters / batches / docs)

_Updated as the run proceeds._

## Flips verified

## Contradictions

## Doc-drift

## Hygiene fixes

## Codex corrections applied (mechanical, evidence-cited)

## Filed

## Archive candidates (operator review)

## Refuted (dropped by verify)

## Plans not reached

## Progress Log

- **2026-08-10** — plan_reconciler dispatch `agt-ec1688` started. Confirmed 23-doc `ui` tranche membership via
  multi-line-aware frontmatter scan (the plain single-line grep undercounts — `asset_group:` often wraps its `[ui]`
  value to the next line). Grace set: 2 docs (`data_status_tab_and_downloads_remediation_2026_06_16.md`, 5h;
  `ui_satellite_ao_dispatch_batch3_2026_08_09.md`, 6h) — read-only this run. Re-verified all 6 items filed by the
  2026-08-07 run: (1) the 4 missed-flip candidates in `data_status_tab_and_downloads_remediation` remain open AND still
  locked AND now additionally grace-protected — cannot act; (2) the
  `deployment_ui_smoke_failures_daily_costs_nav_mobile` archive candidate remains locked
  (`locked_by: live-defi-rollout`, `locked_since: 2026-05-21`, still predates its own `created: 2026-07-21`) — now 5
  consecutive audit passes (2026-08-06/07/08/09 + this one) with zero resolution; (3)
  `deployment_registry_firestore_p5_verify` stale-draft gate unchanged, still behind P3 cutover; (4) the
  `ui_consolidated_closeout` Track 3/4 stale prose remains correctly tracked (not re-filed) — `batch1_finalize` todo 4
  (archival) is "now dispatchable" per its own Progress Log but has not yet run; (5) `plans/active/ACTIVE_INDEX.md`
  confirmed still nonexistent — it is a stale reference inside `plan-reconcile/SKILL.md` / `agents/plan_reconciler.md`
  themselves (both outside `plans/**`, out of my write-scope — flagged, not fixed); (6) hygiene sweep hard-failure set
  has CHANGED since 2026-08-07 (was: reference-path/AG-closeout-linkage/terminal-status-archived/archive-candidates;
  now: proseWrap/reference-path/NA-corpus-size) — corpus-wide, not ui-specific, no action here. **New finding this
  run**: `locked_by: live-defi-rollout` is traced to a hardcoded placeholder in
  `scripts/plans/fix_epic_frontmatter_2026_05_21.py:133` (`lines.append("locked_by: live-defi-rollout")`) — not a real
  actor/agent/operator identity (no one is named after the branch). Corpus-wide grep: 96 docs in `plans/active`+`issues`
  alone carry this exact value, versus legitimate agent locks which carry a real dispatch id + timestamp (e.g.
  `plan_reconciler (agt-xxxxxx) since <ts>`). The `deployment_ui_smoke_failures` doc's `locked_since: 2026-05-21`
  matches this script's own date exactly. Filed as a dedicated cross-cutting issue (see Filed section) since fixing it
  corpus-wide is out of this ui-scoped run's mandate, but it directly blocks a ui-tranche archival decision. Fan-out
  hunters dispatched next for fresh contradiction/hygiene/AO-readiness/ codex-alignment coverage.
