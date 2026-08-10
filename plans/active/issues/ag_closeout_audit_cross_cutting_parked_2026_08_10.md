---
doc_type: issue
title:
  "Parked findings from the 2026-08-10 /ag-closeout-audit cross-cutting run (6 real orphans classified — 3 credential
  asks, 3 other operator-gated; 0 AO-eligible, 0 new)"
summary: >-
  The 2026-08-10 `/ag-closeout-audit all` run's cross-cutting tranche found 6 corpus-confirmed orphans (via
  `check_ag_closeout_linkage.py`) among the tranche's candidate docs. All 6 got a real Phase-1 classification (Workflow,
  one agent per doc): 3 are genuine credential/subscription asks (`databento_ice_opra_subscription_ask`,
  `glassnode_kaiko_credential_ask`, `sportradar_credential_ask` — all correctly named and blocked on operator-only GSM
  secret provisioning / billing decisions), 3 are other operator-gated judgment calls (a live wedge-recovery park/unpark
  decision, a rate-limit-probe design-spec gap, and a stalled backfill-VM manual relaunch). 0 are AO-eligible; 0 new
  batch todos drafted for this tranche this run.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cross-cutting, ag-closeout-audit, parked-findings, credential-ask, operator-gated]
related:
  [
    /plans/active/issues/citadel_satellite_ao_dispatch_batch1_004_repeat_wedge_parked_2026_08_08.md,
    /plans/active/issues/databento_ice_opra_subscription_ask_2026_08_09.md,
    /plans/active/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md,
    /plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md,
    /plans/active/issues/rate_limit_probe_vm_authorized_no_design_spec_2026_08_09.md,
    /plans/active/issues/sportradar_credential_ask_2026_08_09.md,
    /plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md,
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-10"
author: "slot-26 (ag_closeout_auditor, all-tranche mode)"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope: [/scripts/plan-hygiene/check_ag_closeout_linkage.py, /cursor-configs/skills/ag-closeout-audit/SKILL.md]
source: >-
  `/ag-closeout-audit all` run 2026-08-10 (ag_closeout_auditor scheduled worker, slot 26, one-shot, no $TRANCHE set).
  Phase 1 ran a Workflow (one agent per doc, medium effort) over all 6 cross-cutting orphan candidates confirmed by
  `check_ag_closeout_linkage.py`.
---

# Parked findings — 2026-08-10 `/ag-closeout-audit cross-cutting` (part of the `all`-mode run)

## Carried forward, still OPEN (re-verified live this run via real Phase-1 agent classification)

1. **`citadel_satellite_ao_dispatch_batch1_004_repeat_wedge_parked_2026_08_08.md`** (3 open todos) — verdict
   `operator_gated_other`. Todo 1 (BACKEND) needs a cross-task workload-comparison judgment call; todo 2 (`[OPERATOR]`)
   is the real blocker — a 2026-08-09 interactive session already did the analysis (LEAN UNPARK) but could not call the
   unpark API itself, leaving a literal operator dashboard click + residual-risk judgment; todo 3 is gated on todo 2.
   Not AO-eligible.
2. **`databento_ice_opra_subscription_ask_2026_08_09.md`** (2 open todos) — verdict `operator_gated_credential_ask`.
   Item 1 is a billing decision (add ICE/OPRA subscription to the existing Databento account); item 2 (code: add dataset
   codes to the allowlist) is explicitly gated on item 1's approval. Genuine subscription-ask, not AO-eligible.
3. **`escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md`** (1 open todo of 4) — verdict
   `operator_gated_other`. 3 of 4 todos resolved this run's classification confirmed (DP-FETCH-009 investigation already
   handled elsewhere; code-fix REVIEW todo shipped `agent-orchestrator@884a9bfe1`; the P2 historical-sample-audit todo
   satellite-extracted to `cross_cutting_satellite_ao_dispatch_batch7_2026_08_09.md`, now archived complete). The sole
   remaining `[OPERATOR] P1` todo (DP-VM-003, a stalled backfill VM needing manual relaunch) is genuinely operator-gated
   — not a worker-executable audit. **Note**: this doc's own checkboxes for the 3 resolved items may still read `- [ ]`
   in the live corpus; whoever owns this tranche next should verify and flip them with the cited evidence
   (agent-orchestrator@884a9bfe1, the archived batch7 path) rather than re-investigating.
4. **`glassnode_kaiko_credential_ask_2026_08_09.md`** (3 open todos) — verdict `operator_gated_credential_ask`. All 3
   (promote GlassnodeAdapter + KaikoAdapter into `VENUE_REGISTRY`, add live-credential integration tests) are gated on 2
   GSM secrets that do not exist yet (`glassnode-api-key`, `kaiko-api-key`, confirmed via live `gcloud secrets list`).
   `BLOCKED-CREDENTIALS` by the doc's own status. Not AO-eligible even once credentials land — the wiring todos
   explicitly require a downstream-consumer design decision too.
5. **`rate_limit_probe_vm_authorized_no_design_spec_2026_08_09.md`** (1 open todo, `[OPERATOR]`) — verdict
   `operator_gated_other`. The 2026-08-06 operator ruling only answered the risk-tolerance question ("go ahead"), not
   the engineering-spec question (target vendor/endpoint, request pattern, disposable-IP mechanism, stop criteria). The
   2026-08-09 relayed ruling (BLK-04a2a05a) is authoritative: file it, leave the checkbox open, do not invent a design.
   Genuine design-decision gate.
6. **`sportradar_credential_ask_2026_08_09.md`** (2 open todos) — verdict `operator_gated_credential_ask`. Item 1 is an
   `[OPERATOR]` scope decision (Sportradar for schedule/results vs odds, given Odds-API/footystats overlap); item 2
   (registration) is `BLOCKED-CREDENTIALS` on `sportradar-api-key` AND item 1's scope decision. Genuine credential ask.

## Todos

- [ ] [OPERATOR] P2. **Click "unpark" for citadel task -004** in
      `citadel_satellite_ao_dispatch_batch1_004_repeat_wedge_parked_2026_08_08.md` (finding 1) — a 2026-08-09 session's
      LEAN-UNPARK analysis is already in hand; the dashboard action itself needs an operator.
- [ ] [OPERATOR] P3. **Approve/decline the ICE/OPRA Databento subscription add** (finding 2,
      `databento_ice_opra_subscription_ask_2026_08_09.md`) — billing decision.
- [ ] [DOCS] P2. **Verify + flip 3 already-resolved checkboxes** in
      `escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md` (finding 3) — evidence already
      cited above, just needs a doc-only reconciliation pass.
- [ ] [OPERATOR] P1. **Manually relaunch stalled backfill VM DP-VM-003** (finding 3's remaining item).
- [ ] [OPERATOR] P3. **Provision `glassnode-api-key` + `kaiko-api-key` GSM secrets, or decline** (finding 4,
      `glassnode_kaiko_credential_ask_2026_08_09.md`).
- [ ] [OPERATOR] P2. **Supply the rate-limit-probe engineering spec** (finding 5,
      `rate_limit_probe_vm_authorized_no_design_spec_2026_08_09.md`) — vendor/endpoint, request pattern, disposable-IP
      mechanism, stop criteria.
- [ ] [OPERATOR] P3. **Provision `sportradar-api-key` + decide Sportradar's scope, or decline** (finding 6,
      `sportradar_credential_ask_2026_08_09.md`).

## Progress Log

- **2026-08-10** — `/ag-closeout-audit all` run (autonomous mode, task-less one-off, slot 26). Phase 0: corpus-wide
  `check_ag_closeout_linkage.py` confirmed 6 cross-cutting orphans (unchanged before/after this tranche's own linkage
  fixes — none of the 6 were mechanical linkage-only gaps, all genuine). Phase 1: Workflow classification (6 agents,
  medium effort) — 3 `operator_gated_credential_ask`, 3 `operator_gated_other`, 0 AO-eligible. Ledger: 6 findings
  re-verified/carried (all previously known per the 2026-08-08/09 predecessor reports cited in `related:`, no genuinely
  new content this run) + 0 new batch todos — **balanced**.
