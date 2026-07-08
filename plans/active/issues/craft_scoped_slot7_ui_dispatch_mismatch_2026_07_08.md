---
doc_type: issue
title: Slot 7 (data_engineering craft-scoped) dispatched a ui-developer task
summary: |
  A data_engineering-craft-scoped worker slot (7) received a pure UI task
  (`cost_obs_ui_unified_breakdown-008`, role `ui-developer`, repo `deployment-ui`)
  on `/boot`. Filed so the dispatcher's role-affinity routing can be checked for
  why a UI-tagged task reached a data-only slot; slot 7 skipped the task rather
  than cross craft lines.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [dispatch, role-routing, craft-scoping, worker-lifecycle]
related: [cost_obs_ui_unified_breakdown_2026_07_08.md]
created: "2026-07-08"
author: slot-7
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
source: [cost_obs_ui_unified_breakdown_2026_07_08.md]
resolved_by:
locked_by:
---

## What I found

Slot 7's session is craft-scoped to `data_engineering` (pipeline code only: manifests, capture_status,
sourcing/pipeline_mode, GCS writers/readers, backfills — UI/infra/strategy math explicitly out of scope per this slot's
boot instructions). On `/boot`, the dispatcher handed slot 7 task `cost_obs_ui_unified_breakdown-008` —
`assigned_role: ui-developer`, `repos: [deployment-ui]`, TS/Playwright work in
`plans/active/cost_obs_ui_unified_breakdown_2026_07_08.md` (item 8, "Stale-during-refetch fix",
`src/pages/CostObservability.tsx`). This is pure UI craft with no data-pipeline component.

## Why it matters

Slot 7's craft-scoping is a hard boundary (not a preference) — its boot instructions say a mis-scoped dispatch should be
escalated, not absorbed. Doing UI work from this slot would violate that boundary and skip the UI craft's `pw:L2` gate
discipline this task actually needs. The dispatcher's role-affinity routing let a `ui-developer` task reach a
`data_engineering`-only slot — either slot 7's role tag isn't registered/considered by the dispatcher's role-based
routing, or no `ui-developer`-capable slot was free and it fell through to any-slot dispatch.

## Recommended decision

- Slot 7 is calling `/skip-current-task` on `cost_obs_ui_unified_breakdown-008` (reason: craft mismatch) so it returns
  to `queued` for a UI-capable worker.
- [ ] [INFRA] P2. Check the role-dispatch routing (`agent-orchestrator/server/`, role registry) for why a
      `ui-developer`-tagged task was offered to a slot without that role registered — confirm slot-role registration is
      wired for slot 7, or tighten the any-slot fallback so data-only slots aren't offered UI tasks (repo:
      agent-orchestrator).
