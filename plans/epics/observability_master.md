---
doc_type: epic
title: Observability Master
summary:
  L4 cross-cutting epic owning alerting-service + monitoring/telemetry + the Incident Gateway 13-state machine + the
  5-layer recovery defence-in-depth (L0 Python scripts → L1 LLM audit → L2 PagerDuty → L3 Twilio voice → L4 pager → L5
  human ack) + kill-switch/drawdown alerting + the deployment-UI Safety Ops manual-override tab + runbook governance.
  Also owns (folded 2026-08-18) the role-agnostic escalation pipeline + disaster-recovery substrate, formerly a
  separate 1-reference epic.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, deployment-ui]
scope: [engineer, admin]
tags: [observability, monitoring, escalation, self-healing, slack, runbook, live-trading, ui, disaster-recovery, blocked-questions, auto-recovery]
related:
  [
    ../archive/2026_05/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md,
    ../archive/2026_05/alerting_service_live_rules_2026_05_07.md,
    ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md,
    ../archive/incident_gateway_and_state_machine_2026_05_23.plan.md,
    ../archive/2026_05/agent_recovery_controller_layer0_deterministic_2026_05_23.md,
    ../archive/ai_recovery_audit_signoff_agent_2026_05_23.plan.md,
    ../archive/reconciliation_age_tracking_and_escalation_2026_05_23.plan.md,
    ../archive/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.plan.md,
    ../archive/2026_05/connectivity_dependency_buffer_policy_2026_05_23.md,
    ../archive/2026_05/audit_acknowledgement_sla_and_state_2026_05_23.md,
    ../archive/independent_fallback_twilio_voice_2026_05_23.plan.md,
    ../archive/2026_05/physical_pager_research_and_webhook_prototype_2026_05_23.md,
    ../archive/2026_05/incident_runbooks_and_evidence_store_2026_05_23.md,
    ../archive/2026_05/deployment_ui_safety_ops_tab_2026_05_23.md,
    ../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md,
    /plans/epics/escalation_and_disaster_recovery_master.md,
  ]
created: 2026-05-21
name: observability_master
tier: L4
priority: P0
assigned_vm:
  vm-cross-cutting # REVERTED 2026-08-10 (plan_reconciler) -- my own 2026-08-10 edit to NA was WRONG, self-caught same
  # run: `instruments_master.md`/`sports_master.md` carry an explicit, on-the-record ruling
  # (finding 123/262, 2026-07-12, §A2 B-queue) that legacy vm-<id> epic values are RETAINED WORKSPACE-WIDE, no value
  # change, migration out of scope -- distinct from the "was: planning" pattern the 2026-08-02/06 § 2e fixes actually
  # addressed (agent_operating_framework_master/orchestrator_master/plan_hygiene_master all had the MISLEADING
  # `planning` value, not a legacy vm-id). PLAN_FORMAT.md's "a legacy vm-<id> still validates... archaeology, never
  # dispatch-resolved" already covers this value as sanctioned, not stale.
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
  - ../archive/2026_08/alerting_service_lifecycle_events_sub_dual_consumer_slack_spam_2026_08_07_finalize_2026_08_09.md
  - ../active/artifact_pipeline_observability_2026_07_17.md
  - ../active/consolidator_throughput_backlog_monitor_2026_07_09.md
  - /plans/archive/2026_08/data_feed_sla_registry_and_active_self_healing_2026_06_19.md
  - ../active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md
  - ../archive/2026_08/data_pipeline_alerts_batch_remediation_2026_07_15.md
  - ../active/data_pipeline_self_healing_completion_residual_2026_07_24.md
  - ../active/deployment_registry_firestore_migration_2026_07_14.md
  - ../active/deployment_registry_firestore_p3_cutover_2026_07_14.md
  - ../active/monitoring_control_plane_master_2026_06_10.md
  - ../active/orchestrator_vm_e2e_hardening_2026_07_24.md
  - ../active/ui_satellite_ao_dispatch_batch3_2026_08_09.md
  - ../active/ui_satellite_ao_dispatch_batch3_finalize_2026_08_09.md
  - ../active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md
  - ../active/data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15.md
  - ../active/data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15_finalize.md
  - ../active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md
  - ../active/deployment_api_true_catalogue_expected_universe_projection_ao_dispatch_2026_08_16.md
  - ../active/deployment_api_true_catalogue_expected_universe_projection_ao_dispatch_2026_08_16_finalize.md
  - ../active/deployment_registry_firestore_p5_verify_2026_07_14.md
  - ../active/dp_audit_escalation_agent_backed_filing_2026_08_18.md
  - ../active/producer_silence_flatten_protocol_2026_08_14.md
last_updated: 2026-08-19 # was 2026-08-18 -- plan-reconcile observability_master: related_plans roster was stale, 8
# parent_epic:observability_master active/draft plans missing (found by 2 independent hunters); added below
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Observability Master

## Report

Live HTML ledger: https://claude.ai/code/artifact/d5c03be2-274c-4d4c-aea1-b4c9d144661b (generated 2026-08-19,
`/plan-reconcile observability_master`)

**Owns**: alerting-service + monitoring + telemetry + **Incident Gateway state machine** + **Agent Recovery Controller
(Layer-0 deterministic scripts)** + **LLM recovery-audit-signoff agent (Layer-1)** + **reconciliation age tracking** +
**drawdown + liquidation policy + strategy risk config** + **connectivity dependency buffers** + **alert-provider
health + Twilio voice fallback (Layer-3)** + **physical pager layer (Layer-4)** + **audit acknowledgement SLA
(Layer-5)** + **deployment-UI Safety Ops tab (manual override)** + 3am-auto-recovery agent + QG snapshot cron + runbook
governance. Also owns (folded 2026-08-18, see below): the role-agnostic escalation pipeline (blocked → Slack →
human-resolve → UI) + the self-healing/auto-recovery substrate every agent role escalates through.

**Status**: P0-expanded 2026-05-23 — 11 new active plans landed from
[`../audit/results/observability_disaster_recovery_audit_2026_05_23.md`](../audit/results/observability_disaster_recovery_audit_2026_05_23.md)
(gap analysis vs target model in [`../active/issues/disaster_recovery.md`](../active/issues/disaster_recovery.md)).
Total ~86 cal AI-days dispatched across slots for May-23 cutover.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Codex SSOTs

| Doc                                                          | Owns                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/codex/05-infrastructure/live-deployment-monitoring.md`     | Per-archetype heartbeat thresholds; STARTED/progress/STOPPED/FAILED event cadence; cross-cloud event-stream parity                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `/codex/03-observability/alerting.md`                        | AlertSeverity enum (CRITICAL/HIGH/WARN/INFO) → PagerDuty P-tier → routing channels                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `/codex/04-architecture/kill-switch-circuit-breaker.md`      | Kill-switch alerting; circuit-breaker trigger → auto-STOPPED event; alert escalation on arm                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `/codex/04-architecture/autonomous-recovery-matrix.md`       | Decision tree — every failure scenario × every recovery action                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `/codex/04-architecture/incident-gateway-state-machine.md`   | **NEW 2026-05-23** — 13-state incident lifecycle (DETECTED → … → CLOSED); audit-ack queue; dedup-key                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `/codex/04-architecture/recovery-defence-in-depth-layers.md` | **NEW 2026-05-23** — 5-layer model: L0 Python → L1 LLM audit → L2 PagerDuty → L3 Twilio voice → L4 pager → L5 human audit ack                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `/codex/05-infrastructure/disaster-recovery.md`              | RTO/RPO targets, Tier 0-3 recovery, restore from manifest (existing — extended 2026-05-23)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `/codex/15-runbooks/physical-pager-layer.md`                 | **NEW 2026-05-23** — Pager device comparison, webhook prototype, Twilio voice bridge                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `/codex/15-runbooks/alerting/pagerduty-escalation-policy.md` | Ikenna 14:30–02:30 UK / Harsh 02:30–14:30 UK; PagerDuty escalation ladder                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `/codex/15-runbooks/alerting/audit-acknowledgement-flow.md`  | **NEW 2026-05-23** — 6h audit-ack SLA + secondary-human + founder fallback                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `/codex/05-infrastructure/manifest-consolidator-ssot.md`     | Manifest consolidator freshness alerts; silence > 120s → CRITICAL — **[doc-reconciliation 2026-07-12, finding 205, §A2 B-queue ruling] STALE AS A UNIVERSAL RULE** (was: blanket 120s with no exception noted): `active/consolidator_throughput_backlog_monitor_2026_07_09.md` item 5 (`[x]`, shipped `deployment-api@90ace9f`, confirmed on `live-defi-rollout` via `git log`/`git branch --contains` in this pass) proved 120s false-degrades cefi (a daily-batch AG) and introduced a per-AG `_AG_STALENESS_BUDGET_SEC`/`_budget_for` (cefi=86400s, others default 120s). **(was: "Re-read the codex doc in this pass — it still states only the blanket 120s rule (no per-AG exception); the plan's own `[DOCS]` codex-update todo for this exact doc is still unchecked" — that claim was stale/incorrect: the plan's `[DOCS]` P2 item (`consolidator_throughput_backlog_monitor_2026_07_09.md:197`) is `[x]` DONE 2026-07-11, and the codex doc's own "Cockpit data-correctness signals..." section [WS-3, 2026-07-11] already documents the exact per-AG exception, plus a further "Corrected 2026-07-12 (finding 205)" note with `_AG_STALENESS_BUDGET_SEC={"cefi": 86400}` — both verified present. [finding 181, synced 2026-07-14])** |
| `/codex/02-data/data-pipeline-correctness-hard-rule.md`      | Layer freeze on RED data audit; slot-reassignment trigger                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

## Assigned active plans

_19 plans declare `parent_epic: observability_master` in their frontmatter (18 `status: active` + 1 `status: draft` —
corrected 2026-08-19, plan-reconcile: was stale at "13", 6 active + the 1 draft were missing from both this count
and `related_plans:` above). Workers pick up in priority order (P0 first). The P0-P3 breakdown below has not been
regenerated for the 6 newly-added active plans yet (`scripts/plans/populate_epic_bodies_2026_05_21.py` scope-touches
every epic in the corpus, out of scope for this epic-only pass) — see `related_plans:` frontmatter for the full
current roster until the next full regen; the 6 not yet placed into a priority tier: `data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15`
(+`_finalize`), `data_pipeline_alert_storm_root_cause_batch_2026_08_10`,
`deployment_api_true_catalogue_expected_universe_projection_ao_dispatch_2026_08_16` (+`_finalize`),
`dp_audit_escalation_agent_backed_filing_2026_08_18`, `producer_silence_flatten_protocol_2026_08_14`._

## P0 — must complete before next foundation gate

### [`data_feed_sla_registry_and_active_self_healing_2026_06_19`](/plans/archive/2026_08/data_feed_sla_registry_and_active_self_healing_2026_06_19.md)

**status**: active · **estimate**: 3.0 cal AI-days (class: design) **title**: Data-feed SLA registry (single SSOT) +
active feed self-healing

### [`deployment_registry_firestore_migration_2026_07_14`](../active/deployment_registry_firestore_migration_2026_07_14.md)

**status**: active · **estimate**: 13 cal AI-days (class: infra) **title**: Deployment registry — migrate from
GCS-object-per-VM to Firestore (queryable, scalable, AWS-ready) — OVERVIEW

### [`monitoring_control_plane_master_2026_06_10`](../active/monitoring_control_plane_master_2026_06_10.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: design) **title**: Monitoring control-plane master — CI
dashboard (deployment-ui) + fleet git-health (orchestrator)

### [`orchestrator_vm_e2e_hardening_2026_07_24`](../active/orchestrator_vm_e2e_hardening_2026_07_24.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: design) **title**: Orchestrator e2e control-plane
validation + VM-from-scratch hardening

## P1 — important; post-current-gate

### [`data_pipeline_ag_residual_backfill_decisions_2026_07_24`](../active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md)

**status**: active · **estimate**: 1.6 cal AI-days (class: infra) **title**: Data-Pipeline AG Residual Backfill
Decisions — TradFi + DeFi (forked from the hardening/self-monitoring plan)

### [`deployment_registry_firestore_p3_cutover_2026_07_14`](../active/deployment_registry_firestore_p3_cutover_2026_07_14.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: Deployment registry Firestore migration —
Phase 3 — cutover to Firestore-only + decommission the GCS registry

## P2 — useful; opportunistic

### [`artifact_pipeline_observability_2026_07_17`](../active/artifact_pipeline_observability_2026_07_17.md)

**status**: active · **estimate**: 10 cal AI-days (class: infra) **title**: Artifact pipeline observability — build →
artifact → deploy lineage across both clouds

### [`consolidator_throughput_backlog_monitor_2026_07_09`](../active/consolidator_throughput_backlog_monitor_2026_07_09.md)

**status**: active · **estimate**: 1.8 cal AI-days (class: design) **title**: Consolidators tab — per-AG backlog +
consolidation throughput monitor

### [`data_pipeline_self_healing_completion_residual_2026_07_24`](../active/data_pipeline_self_healing_completion_residual_2026_07_24.md)

**status**: active · **estimate**: 2 cal AI-days (class: infra) **title**: Data-Pipeline Self-Healing Completion —
Residual Actuator Wiring (forked from the hardening/self-monitoring plan)

## P3 — backlog; revisit quarterly

### [`alerting_service_lifecycle_events_sub_dual_consumer_slack_spam_2026_08_07_finalize_2026_08_09`](../archive/2026_08/alerting_service_lifecycle_events_sub_dual_consumer_slack_spam_2026_08_07_finalize_2026_08_09.md)

**status**: active · **estimate**: 0.16 cal AI-days (class: infra) **title**: >-

### [`ui_satellite_ao_dispatch_batch3_2026_08_09`](../active/ui_satellite_ao_dispatch_batch3_2026_08_09.md)

**status**: active · **estimate**: 0.32 cal AI-days (class: infra)

### [`ui_satellite_ao_dispatch_batch3_finalize_2026_08_09`](../active/ui_satellite_ao_dispatch_batch3_finalize_2026_08_09.md)

**status**: active · **estimate**: 0.16 cal AI-days (class: infra) **title**: UI satellite AO batch 3 — finalize
(reconcile source doc + archive)

## Folded-in scope 2026-07-15 (plan-reconcile §6)

- [ ] [REVIEW] P3. WS-4 (verify): re-pull a 24–48 h `#ci-failures` window post-rollout and confirm the volume drop
      (promotion-lag re-reminds ~2 h not hourly, no green all-clears, QG failures dedup per-branch); drop the evidence
      jsonl in `alerts_audit/`. (Pure observation window — same 24–48 h wait as AO WS-E.) (FOLDED IN from
      ci_failures_channel_cleanup_2026_07_13, 2026-07-15, plan-reconcile §6 operator ruling)

## Folded-in scope 2026-07-21 (plan-reconcile consolidation pass)

- [ ] [BACKEND] P3. **LIVE/PAPER `stalled` signals — DEFERRED (scope decision 2026-07-10, needs new subsystems)**.
      Discovered while wiring the BATCH row (deployment-api@29f3be5): LIVE `stalled` needs an expected-active-window
      calendar (market-hours-aware, so an idle-but-healthy off-hours window never misfires); PAPER needs a `work_delta`
      (rows-out-delta) tracker (the D.1 rolling window @970bcdc samples `/proc` cpu/mem/disk, NOT `rows_out`, so it
      would have to be extended to carry the counter history first). **Decision**: both are genuinely NEW subsystems — a
      market calendar and a counter-history tracker — disproportionate to build for a P3 `stalled` refinement, so they
      are DEFERRED to a future phase. The current **honest-`"unknown"` degradation is confirmed correct** as the v1:
      `_composite_health_status` returns `"unknown"` for LIVE/PAPER `stalled` rather than guessing from a proxy (WS-D.0
      principle 2), and the oom-risk/`stalled` alert wiring (deployment-api@5e25dce) only fires on a REAL state, so
      nothing misfires while these stay unknown. BATCH — the one umbrella with a real signal (`object_delta`) — is
      wired + shipped. This item stays open (not a fake `[x]`) as an explicit, tracked deferral. No sibling plan under
      this epic owns VM/job work-health signals or a market-hours calendar today (checked
      `consolidator_throughput_backlog_monitor_2026_07_09.md` — different surface, backlog/throughput not
      liveness-stalled detection). (FOLDED IN from deployment_observability_expansion_2026_07_08.md, originally from
      deployment_obs_backend_kinds_health_2026_07_09, via 2026-07-15 plan-reconcile §6 operator ruling — second-hop fold
      2026-07-21, source plan archived)

## Folded-in epic: Escalation & Disaster Recovery Master (folded 2026-08-18)

**Source**: [`escalation_and_disaster_recovery_master.md`](escalation_and_disaster_recovery_master.md) (193 lines, 1
corpus reference at fold time) — folded into this epic per
[`/codex/11-project-management/epic-taxonomy-2026-08-18.md`](/codex/11-project-management/epic-taxonomy-2026-08-18.md)
(domain 4, Deployment & observability). The source file is kept as archaeology, `status: superseded`, with a banner
pointing here — do not add new work there. The 1 referencing doc
([`blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`](../active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md))
had its `parent_epic:` frontmatter updated to `observability_master` in the same pass.

**Owns**: the one path every agent role takes when it cannot self-resolve — and the self-healing substrate that keeps
that path rare. Role-agnostic escalation pipeline (blocked → Slack → human-resolve → UI). Design target: **95%
self-resolution** — an agent exhausts its own tools + asks peer roles before anything reaches a human. When it must
escalate, it escalates **once, cleanly, with options it already researched**, and the whole lifecycle is **always
visible + always resolvable** in one UI.

This is **role-agnostic infrastructure**. Each role (Data-Eng, DevOps, QA, …) declares its escalation triggers in its
own role-registry charter (`agent_operating_framework_master`); this section owns the _pipeline_ those triggers flow
through.

**Repos**: agent-orchestrator, alerting-service, deployment-ui.

**Assigned active plans**: none declared `parent_epic: escalation_and_disaster_recovery_master` at fold time — new
work in this area now declares `parent_epic: observability_master`.

### Why this section exists

Today the blocked-question loop is built end-to-end but role-blind and operator-secondary:

- `POST /api/slots/{id}/blocked` → SQLite `BlockedRow` (question + `options[]` + `recommendation`) → Slack alert
  with a dashboard deep-link → dashboard `BlockedCard` (option buttons + "Other" free-text + role selector) →
  `POST /api/blocked/{id}/answer` → worker polls the answer. **BUILT** — see
  `/codex/04-architecture/agent-orchestrator-overview.md`.
- `alerting-service` fans `DP_*` / kill-switch / recon / deployment events to Slack `#data-pipeline-alerts` /
  `#uts-live-alerts`. **BUILT** but fire-and-forget (one-way webhook, no interactive resolution, no alert state).
- The auto-recovery matrix (`/codex/04-architecture/autonomous-recovery-matrix.md`) defines what arms/un-kills
  autonomously vs `manual_unkill` (human-only). **BUILT** as the kill-switch governance.

Three gaps separate this from the operator's vision (operator design pass, 2026-06-25):

1. **The Slack link goes to the _whole_ blocked queue, not a scoped single-question page** — the human has to hunt.
2. **No alert state** — there's no `open / in-progress / resolved` lifecycle a human can filter on; no "someone is
   working on this" intermediate so two operators don't collide.
3. **Escalation is not generalized across roles** — `/blocked` is worker→main→operator; there is no uniform "role R
   hit a wall, route the decision to the human with R's pre-researched options" entry point that any role
   (Data-Eng audit, DevOps CI-wall, QA UAT) uses identically.

### Target pipeline (role-agnostic)

```
agent (any role) hits a wall
   → self-resolve attempts exhausted (autonomy gradient: Proceed)
   → ask peer roles via broker (if available)     ── 95% resolved here
   → still blocked → ESCALATE (autonomy gradient: Escalate-non-blocking | Gate)
       → one durable escalation record { role, domain, question, options[], recommendation, severity, state }
       → ONE Slack alert  → scoped link → /escalation/{id}  (just this question + its options)
       → human: pick an option | "Other" free-text | "I'm on it" (→ in-progress)
       → resolved → answer routed back to the originating agent
   → always visible in deployment-ui; filter open vs in-progress vs resolved; resolved stay browsable
```

**Self-healing first**: most "escalations" are rule-based and never need a human (dirty repo too long, stale
worker, tmux lost, CI label mismatch). Those are handled by the existing AutoSpawn / liveness / pruner mechanisms +
the auto-recovery matrix. This section only routes to a human for the **`manual_unkill` / operator-decision**
residue.

### Escalation workstream registry (child plans)

| WS  | Child plan                                                                                                  | Scope                                                                                                                                    | Depends                                                                             | Priority | Status                                                                                                                                          |
| --- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| E1  | `escalation_pipeline_mvp_2026_06_25` → [ARCHIVED](../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md) | Generalize `/blocked` → role-agnostic escalation record + `open/in-progress/resolved` state + scoped Slack link + close the 3 gaps      | none (broker dependency retired 2026-07-16, superseded by `assigned_role` dispatch) | P1       | **tracked in this section, ACTIVE** — child plan archived 2026-07-23 as duplicate tracking; its todos live in "Escalation pipeline MVP (P1)" below |
| E2  | _(future)_ slack-interactive-resolve                                                                        | Real Slack app (Block Kit action buttons / `/resolve` slash) so a human answers in Slack without the dashboard hop                       | E1                                                                                    | P2       | deferred                                                                                                                                              |
| E3  | _(future)_ dr-runbook-registry                                                                              | Disaster-recovery runbooks (owner/cadence/verifier/last_executed) wired to the auto-recovery matrix for non-self-healing failure classes | E1                                                                                    | P2       | deferred                                                                                                                                              |

### Escalation composition with other epics

- **`agent_operating_framework_master`** — owns the role registry this pipeline rides on. Roles declare escalation
  triggers there; this section consumes them. E1's dependency on a message broker was retired 2026-07-16
  (superseded by `assigned_role` dispatch); the existing `POST /api/blocked/{id}/answer` → worker-poll path already
  satisfies the reply-routing requirement.
- **This epic (`observability_master`)** — the deployment-ui surfaces + alert-state rendering compose with the
  observability dashboard directly, now that both live in the same file. The "always visible / filter
  open-vs-resolved" UI lands as a deployment-ui tab.
- **`client_isolation_and_governance_master`** — the `manual_unkill` / kill-switch governance that this pipeline's
  human-gated branch defers to (`/codex/04-architecture/autonomous-recovery-matrix.md`).

### Escalation out of scope

- The message broker itself (owned by `agent_operating_framework_master` — this section _consumes_ it, doesn't own
  it).
- Per-role escalation _triggers_ (declared in each role's own registry charter — this section owns the _pipeline_,
  not the triggers).
- A new Slack OAuth app (E2, deferred — the MVP keeps the one-way webhook + dashboard-resolve, just scoped +
  stateful).

### Design input, scoped + shipped 2026-08-10 (was: "awaiting scope")

- [`blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`](../active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md)
  — **corrected 2026-08-19, plan-reconcile observability_master: this section was stale.** The operator ruled scope
  2026-08-08 ("all three: session_id capture + transcript-jump + dedup/similarity") and the doc's own 5 todos were
  all `[x]` by 2026-08-10, each with a HARD-evidence commit (`agent-orchestrator@37f73f9`/`@c6273b2`/`@514df29c07`,
  all re-verified ancestors of `origin/live-defi-rollout` this pass; `claude_session_id` column confirmed live in
  `server/orm.py:176`). `archive_exempt: true` is set deliberately — not because the work is incomplete, but
  because other active docs still cite it as a reference. Was NOT deferred/not-actioned as this section previously
  read; fully shipped.

### Escalation pipeline MVP (P1)

This section is the SINGLE tracking home for E1 (child plan archived 2026-07-23 as duplicate tracking — its 5
todos were absorbed here; 4 were already mirrored verbatim). The design reference (locked design, phased DAG,
gates, success criteria) lives in the archived plan:
[`../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md`](../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md).
Generalize the blocked loop into a role-agnostic, stateful, scoped-link escalation pipeline. **The broker is NOT a
dependency** — that plan was archived as NOT-REQUIRED (superseded by `assigned_role` dispatch), and the reply path
already exists via `POST /api/blocked/{id}/answer`. All 6 todos below (5 original + 1 prerequisite) are real,
fully-scoped, AO-dispatchable work — un-paused 2026-07-28 (operator gated-decision closeout pass).

- [ ] [BACKEND] P0. **Prerequisite — resolve the `/api/escalate` vs `/api/escalation/{id}` route-naming collision**
      BEFORE any of the P1 todos below are coded. `/api/escalate` already exists as the GHA-to-orchestrator CI-wall
      judgment dispatch; this section's target pipeline (see "Target pipeline" above) proposes `/escalation/{id}`
      for the human-facing scoped link — whoever writes the second without noticing the first will either collide
      or wire operator escalations into the CI-judgment path. **Gate**: one of the two routes is renamed (or
      namespaced, e.g. `/api/escalations/{id}` vs the existing CI-wall `/api/escalate`), or a recorded decision
      explains why the near-collision is acceptable — land this BEFORE the role-agnostic escalation record todo
      below. (E1)
- [ ] [CODE] P1. Role-agnostic escalation record
      `{ role, domain, question, options[], recommendation, severity, state }` generalizing `BlockedRow` (additive;
      existing `/blocked` keeps working). (E1)
- [ ] [CODE] P1. `open / in-progress / resolved` state + a `claim` ("I'm on it") transition; resolved rows stay
      browsable + filterable. (E1)
- [ ] [CODE] P1. Scoped Slack link → `/escalation/{id}` (one question + its options), not the whole queue. (E1)
- [ ] [CODE] P1. Resolution routes the answer back to the originating agent — via the EXISTING
      `POST /api/blocked/{id}/answer` → worker-reads-on-next-poll path, **not** a broker `reply_to` (broker retired
      2026-07-16). **Gate**: an answered escalation delivers the choice to a waiting agent (end-to-end test). (E1)
- [ ] [UI] P1. deployment-ui escalation tab: open / in-progress / resolved filter; deep-links to the
      agent-orchestrator resolution surface (defer-unify with `agent_operating_framework_master`'s own UI
      decisions). (E1)

### Escalation deferred (own efforts, P2)

- [ ] [CODE] P2. **E2** — Slack-interactive resolve (Block Kit buttons / slash command) so the human answers in
      Slack.
- [ ] [DOCS] P2. **E3** — DR runbook registry (owner/cadence/verifier/last_executed) for non-self-healing failure
      classes.

### Escalation section Progress Log (carried from the source epic)

- 2026-07-28: **UN-PAUSED** (operator gated-decision closeout pass). `status: paused` → `active`. Added the
  route-naming-collision fix as an explicit P0 prerequisite todo. All 6 todos above (5 original + this prerequisite)
  are real, fully-scoped, AO-dispatchable work — no code shipped that pass, plan-only change.
- 2026-07-23: E1's child plan `escalation_pipeline_mvp_2026_06_25` ARCHIVED (operator instruction); this section
  became its single tracking home. 4 of 5 todos were already mirrored verbatim; the 5th (reply routing) was reworded
  to drop the retired broker `reply_to` in favor of the existing `POST /api/blocked/{id}/answer` path. All 5 todos
  code-verified UNBUILT on 2026-07-16 and stayed wanted.
- 2026-06-25: Section created (as its own epic, pre-fold) in the operator role-registry design pass — split out of
  the cross-agent escalation thread of `agent_operating_framework_master` because it is genuinely distinct
  (role-agnostic pipeline + DR substrate) and composes with this epic (`observability_master`). Three gaps scoped
  (scoped-link / alert-state / role-generalization). E1 (MVP) proposed as the first child plan. E2/E3 deferred.
- 2026-08-18: Folded from the standalone `escalation_and_disaster_recovery_master` epic into this epic per the
  9-domain taxonomy restructure (1 corpus reference at fold time, retagged) — see this section's own header for
  provenance.

## Archived plans

### [`deployment_ui_observability_ux_tracker_2026_07_17`](../archive/2026_07/deployment_ui_observability_ux_tracker_2026_07_17.md)

**status**: ✅ ARCHIVED 2026-07-30 — operator-dictated tracker for 6 deployment-ui observability/UX workstreams
(cost/day accuracy, date-range filter + search, VM log viewer, alerts ingestion + page rebuild, durable
resource-metrics timeline, Fleet-tab consolidation), split into 7 child plans, all shipped + archived 2026-07-20→28.

### [`data_pipeline_alerts_batch_remediation_2026_07_15`](../archive/2026_08/data_pipeline_alerts_batch_remediation_2026_07_15.md)

**status**: ✅ ARCHIVED 2026-08-22 — the doc's last open item (a 24h+ real-wall-clock observation window watching for a
RESOLVED/green bookend) closed with live evidence: 34+ days of production `#data-pipeline-alerts` history confirm the
dedup/RESOLVED-bookend fix works for every sports/tradfi/cefi cell, including `tradfi/mbp_10`. All todos `[x]`, 0 open.
Moved from `plans/active/` to `plans/archive/2026_08/`.

### [`data_pipeline_alerts_batch_remediation_closeout_2026_07_24`](../archive/2026_07/data_pipeline_alerts_batch_remediation_closeout_2026_07_24.md)

**status**: ✅ ARCHIVED 2026-07-24 — closeout & historical narrative for
[`data_pipeline_alerts_batch_remediation_2026_07_15`](../archive/2026_08/data_pipeline_alerts_batch_remediation_2026_07_15.md);
all 14 todos it carried are `[x]`, 0 open. Moved from `plans/active/` to `plans/archive/2026_07/` the same day it was
extracted (plan line-cap remediation) since it was already fully-closed history, not just an over-cap trim.

### [`alerting_service_live_rules_2026_05_07`](../archive/2026_05/alerting_service_live_rules_2026_05_07.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-9 complete. Deferred operator tasks migrated to P3 above.

### [`incident_gateway_and_state_machine_2026_05_23`](../archive/incident_gateway_and_state_machine_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped.

### [`ai_recovery_audit_signoff_agent_2026_05_23`](../archive/ai_recovery_audit_signoff_agent_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All implementable phases shipped. Operator-action items in P3.

### [`reconciliation_age_tracking_and_escalation_2026_05_23`](../archive/reconciliation_age_tracking_and_escalation_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped. Operator smoke in P3.

### [`drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23`](../archive/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped. Operator smoke in P3.

### [`independent_fallback_twilio_voice_2026_05_23`](../archive/independent_fallback_twilio_voice_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — Code shipped. Twilio account creation + creds in P3.
