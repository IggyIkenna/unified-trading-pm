---
doc_type: epic
title: DART + Promote Workflow Master (L3)
summary:
  L3 epic owning the DART operator UX cockpit (ManualTradeGateDialog, manual replication of every live action) + the
  promote workflow (CLI primary / UI secondary, CANDIDATE→PAPER_1D→LIVE_EARLY state machine, MinimalCandidateManifest in
  UAC, Firebase execution-full enforcement); UI ticks gated by the playwright pw:L2 verification contract.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-ui, unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, strategy, execution, live-trading, verification, observability]
related:
  [
    ../archive/2026_05/promote_workflow_may23_cli_path_2026_05_10.md,
    ../archive/2026_05/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md,
    ../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md,
  ]
created: 2026-05-21
name: dart_and_promote_master
tier: L3
priority: P0
assigned_vm: vm-operator-ops
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans: []
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# DART + Promote Workflow Master (L3)

**Owns**: DART operator UX cockpit + `ManualTradeGateDialog` + promote workflow (CLI primary + UI secondary) + strategy
lifecycle state machine + `MinimalCandidateManifest` (UAC) + Firebase `execution-full` enforcement.

**Assigned VM**: `vm-operator-ops` (co-located with `deployment_and_user_management_master`).

**Corrected 2026-07-12** (finding 10008, §A2 B-queue ruling): the `related`/`related_plans` frontmatter path for the
global-ledger discovery plan was `../active/global_ledger_pnl_attribution_discovery_2026_05_21.md` (404s — that plan
archived 2026-05-23; confirmed on disk only under `../archive/2026_05/`) — corrected to
`../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md`.

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

## UI Verification Contract (HARD RULE — codified 2026-05-23)

All active plans under this epic that touch any UI repo (`unified-trading-system-ui`, `deployment-ui` — was: also
`user-management-ui`; ARCHIVED 2026-05, folded into `unified-trading-system-ui` per
`/codex/04-architecture/runtime-deployment-topology.md` + CLAUDE.md's system map; corrected 2026-07-12, findings
310/386, `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 B-queue ruling) MUST pass the
playwright verification gate before any todo is ticked ✅ done. Per `plans/PLAN_FORMAT.md` § 9 and
`/codex/06-coding-standards/ui-testing-layers.md` § "Plan-Level Enforcement":

- **`[UI]` tag**: every UI-touching todo MUST use `[AGENT][UI]` or `[HUMAN][UI]` (not bare `[AGENT]`).
- **pw:L2 ✓**: `npx playwright test --project=chromium tests/smoke/` exits 0 before tick.
- **regression guard**: spec written/updated in `tests/e2e/`, `tests/playbooks/`, `tests/widgets/`, or `tests/smoke/`
  matched to the change layer (widget→L1.5, route→L2, playbook flow→L3a, strategy execute→L3b, visual→L4).
- **Evidence format**: `— repo@sha | pw:L2 ✓ | regression: tests/path/spec.ts` appended to tick line.
- **Reviewer rejects** ticks missing `pw:` or `regression:` — same weight as a missing `docs(plans):` flip.

Key DART/promote surfaces and their required layers:

| Surface                       | Layer | Regression guard path                            |
| ----------------------------- | ----- | ------------------------------------------------ |
| ManualTradeGateDialog         | L3a   | `tests/playbooks/promote_workflow.spec.ts`       |
| Promote button → API call     | L3a   | `tests/playbooks/promote_workflow.spec.ts`       |
| DART cockpit route loads      | L2    | `tests/smoke/routes.spec.ts`                     |
| Strategy lifecycle state chip | L1.5  | `tests/widgets/strategy-lifecycle-chip.test.tsx` |

## Codex SSOTs

- [`/codex/04-architecture/promote-workflow-architecture.md`](/codex/04-architecture/promote-workflow-architecture.md) —
  CLI + UI promote tracks + state machine + candidate manifest
- [`/codex/09-strategy/operational/cli-promote-paths.md`](/codex/09-strategy/operational/cli-promote-paths.md) — CLI
  dispatch pattern
- [`codex/14-customer-journeys/dart/`](../../codex/14-customer-journeys/dart/) — DART terminal vs research playbook

## Composition with other epics

- **Upstream**: `strategy_master` (strategy lifecycle phases drive promote eligibility) + `trading_agent_master`
  (closed-loop allocator emits AllocationDirective consumed by promote)
- **Downstream**: `execution_master` (promote-acked instructions flow to execution)
- **Co-located VM**: `deployment_and_user_management_master` (deployment-api Promote button + Firebase auth)
- **Cross-cutting**: `client_isolation_and_governance_master` (manual-trade gate enforces per-client + per-jurisdiction)

## Assigned active plans

_(no active plans currently declare `parent_epic: dart_and_promote_master`. Audit-pool wrapper plans for this epic land
here as they are dispatched. See [README.md](README.md) for the audit→plan→epic flow.)_

## Archived plans

### [`promote_workflow_may23_cli_path_2026_05_10`](../archive/2026_05/promote_workflow_may23_cli_path_2026_05_10.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phase 1 complete; Phases 3-10 and Phase 2 VM smoke deferred.

**Deferred (migrated):**

- **Phases 3-10 (DEFERRED-POST-CUTOVER)**: Full promote-workflow pipeline (Firestore MinimalCandidateManifest write,
  paper VM auto-launch, ManualTradeGateDialog integration, live VM auto-launch, LIVE_EARLY→LIVE graduation, multi-tenant
  flow H4) — all gated on DeFi 7-day soak.
- **Phase 2 smoke VM verification (DEFERRED-OPERATOR)**: Requires `vm-operator-ops` launch to validate CLI promote path
  end-to-end.
- **MinimalCandidateManifest enrichment (DEFERRED-POST-CUTOVER)**: Pinned shas, model refs, features manifest version
  fields.
- **LifecycleEventType UAC enum (DEFERRED-POST-CUTOVER)**: Extend once `strategy_master` lifecycle state machine
  settled.

### [`promote_workflow_post_cutover_ui_pipeline_2026_05_10`](../archive/2026_05/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)

**status**: ✅ ARCHIVED 2026-05-23 — Entire plan DEFERRED-POST-CUTOVER (gated on DeFi 7-day live soak).

**Deferred (migrated):**

- **All 12 phases (DEFERRED-POST-CUTOVER)**: Firebase `execution-full` enforcement, Promote button UI pipeline,
  state-machine consolidation, candidate manifest enrichment, Firestore backend integration, Playwright e2e matrix — all
  blocked until DeFi goes live and completes 7-day soak.
