---
name: dart_and_promote_master
title: "DART + Promote Workflow Master (L3)"
type: epic
tier: L3
status: active
priority: P0
assigned_vm: vm-operator-ops
parent: master_to_live_defi_2026_05_23
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../active/promote_workflow_may23_cli_path_2026_05_10.md
  - ../active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md
  - ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md
---

# DART + Promote Workflow Master (L3)

**Owns**: DART operator UX cockpit + `ManualTradeGateDialog` + promote workflow (CLI primary + UI secondary) + strategy
lifecycle state machine + `MinimalCandidateManifest` (UAC) + Firebase `execution-full` enforcement.

**Assigned VM**: `vm-operator-ops` (co-located with `deployment_and_user_management_master`).

## Scope inherited from `strategy_and_dart_master_SUPERSEDED_2026_05_21` (split 2026-05-21)

The pre-2026-05-21 `strategy_and_dart_master` umbrella was split into two everlasting epics. \*\*This epic owns the DART

- promote side\*\*:

* **DART operator UX cockpit** (was `dart_ux_cockpit_refactor`) — 9-phase programme collapsing DART from a route tree
  into a guided cross-asset trading cockpit. 9 phases + Configuration lifecycle UI surfaces + persona walkthrough
  Playwright matrix + Phase 1A/1B foundational primitives shipped. 7 open polish items: widget vocabulary SSOT,
  cross-cutting widget conventions, Layer-2 minimum proof signals, v2 archetype-expansion roadmap, doc alignment, IR
  copy alignment, public website copy alignment.
* **Promote workflow May-23 dual-track** — CLI primary (`run-paper.sh` → `colocated_engine.py` → `run-live.sh`) + UI
  secondary (Promote button → `MinimalCandidateManifest` in Firestore → paper/live VM auto-launch → DART
  `ManualTradeGateDialog` first 3 trading days). Valid May-23 transitions: `CANDIDATE → PAPER_1D → LIVE_EARLY`.
* **Promote workflow post-cutover UI pipeline** — full state-machine consolidation + candidate manifest enrichment
  (pinned shas, model refs, features manifest version) + Firebase backend integration.
* **UI walkthrough audit + persona walkthrough matrix** — every live action replicable as manual operator action.

Strategy archetype + portfolio_allocator + risk/position/pnl scope went to [`strategy_master.md`](strategy_master.md)
(L2). Full archaeology:
[`strategy_and_dart_master_SUPERSEDED_2026_05_21.md`](strategy_and_dart_master_SUPERSEDED_2026_05_21.md).

## Codex SSOTs

- [`codex/04-architecture/promote-workflow-architecture.md`](../../codex/04-architecture/promote-workflow-architecture.md)
  — CLI + UI promote tracks + state machine + candidate manifest
- [`codex/09-strategy/operational/cli-promote-paths.md`](../../codex/09-strategy/operational/cli-promote-paths.md) — CLI
  dispatch pattern
- [`codex/14-customer-journeys/dart/`](../../codex/14-customer-journeys/dart/) — DART terminal vs research playbook

## Composition with other epics

- **Upstream**: `strategy_master` (strategy lifecycle phases drive promote eligibility) + `trading_agent_master`
  (closed-loop allocator emits AllocationDirective consumed by promote)
- **Downstream**: `execution_master` (promote-acked instructions flow to execution)
- **Co-located VM**: `deployment_and_user_management_master` (deployment-api Promote button + Firebase auth)
- **Cross-cutting**: `client_isolation_and_governance_master` (manual-trade gate enforces per-client + per-jurisdiction)

## Assigned active plans

_2 active plans declare `parent_epic: dart_and_promote_master` in their frontmatter. Workers pick up in priority order
(P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## Assigned active plans

_2 active plans declare `parent_epic: dart_and_promote_master` in their frontmatter. Workers pick up in priority order
(P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

_(no plans currently assigned at this priority)_

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

### [`promote_workflow_may23_cli_path_2026_05_10`](../active/promote_workflow_may23_cli_path_2026_05_10.md)

**status**: active · **estimate**: 4.2 cal AI-days (class: design)

### [`promote_workflow_post_cutover_ui_pipeline_2026_05_10`](../active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)

**status**: active · **estimate**: 20.0 cal AI-days (class: infra)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
