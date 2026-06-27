---
doc_type: plan
title: Monitoring Surfaces Overhaul — SPLIT into two single-surface plans (SUPERSEDED 2026-06-19)
summary:
  Superseded two-track monitoring overhaul plan — split into deployment-ui monitoring pane and agent-orchestrator
  dashboard plans so separate agents can work them without collision.
status: superseded
nature: process
stage: [meta]
repos: [agent-orchestrator, deployment-api, deployment-ui, market-data-processing-service]
scope: [engineer, admin]
tags: [monitoring, deployment-ui, orchestrator, superseded, redirect, observability]
related: []
created: 2026-06-18
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope:
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    2026-06-18 operator design session — orchestrator UI = agents/orchestrator lens; deployment-ui =
    CICD/codebase/fleet/images,
    2026-06-19 operator decision — split into two single-surface plans so the deployment-ui side and the
    agent-orchestrator side can be worked by separate agents without collision,
    "plans/audit/results/monitoring_surfaces_audit_2026_06_18.md (Opus audit, 4 background agents)",
  ]
plan_of_record: plans/active/monitoring_control_plane_master_2026_06_10.md
audit_ref: plans/audit/results/monitoring_surfaces_audit_2026_06_18.md
---

# Monitoring Surfaces Overhaul — SUPERSEDED (split 2026-06-19)

> **SUPERSEDED 2026-06-19.** This two-track plan was split into two single-surface plans so the deployment-ui side and
> the agent-orchestrator side can be worked by **separate agents without collision** (operator decision). All todos
> migrated verbatim — there are **no open items here** (this is a redirect tombstone; the backlog regen reads the two
> children, not this file).

## Where the work went

| Former track                                                     | Successor plan                                                                                                   | Repos                          |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| Track B — deployment-ui monitoring pane + Cloud Build visibility | [`deployment_ui_monitoring_pane_2026_06_19.md`](deployment_ui_monitoring_pane_2026_06_19.md)                     | deployment-ui + deployment-api |
| Track A — agent-orchestrator dashboard                           | [`agent_orchestrator_dashboard_monitoring_2026_06_19.md`](agent_orchestrator_dashboard_monitoring_2026_06_19.md) | agent-orchestrator             |

## What already shipped under this plan (carried into the deployment-ui successor)

- ✅ deployment-api Cloud Build history regional + REPO_NAME-keyed (was always-empty) — deployment-api@5bf7165c.
- ✅ deployment-api triggers pane survives a Redis outage (RedisError now caught, degrades to cache-miss) —
  deployment-api@5bf7165c.
- ✅ market-data-processing-service image build fixed (three stacked causes: `--no-sources`, stale `BASE_IMAGE_DIGEST`
  refresh, in-image QG `CLOUD_BUILD` guard) — mdps@8025264d | Cloud Build `3c501b1f` green end-to-end.

The fleet-wide stale-`BASE_IMAGE_DIGEST`-pin audit (open) lives in the deployment-ui successor.

## Lifecycle

Redirect kept in `plans/active/` because external docs still reference this filename
(`orchestrator_agent_type_oversight_coverage_2026_06_17.md`, the audit doc). Safe to archive once those references are
repointed to the two successor plans.
