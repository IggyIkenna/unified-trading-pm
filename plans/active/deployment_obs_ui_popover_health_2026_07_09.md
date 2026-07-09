---
doc_type: plan
title: Deployment observability — kind badges, composite health, resource columns + detail popover (UI)
summary:
  UI half of the deployment-observability expansion — render the full-estate kinds (6 kind badges), the composite VM
  health chip (7-state, 3-tier severity colour) and the service health states, the cpu/mem/disk Resources columns, a
  Kind filter, and a name-click detail popover (sparklines + timeline + absolute used/total + owning consolidator + an
  "Open in GCP/AWS console" deep-link). Starts draft, released to active by the last task of
  deployment_obs_backend_kinds_health_2026_07_09 once the API contract exists. Every UI task carries a Playwright L2
  regression. Full design + the mock that is the visual contract live in the LOCAL parent
  deployment_observability_expansion_2026_07_08.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [deployment-observability, cockpit, vm-health, ui, deployment-ui, playwright]
related: [deployment_observability_expansion_2026_07_08.md, deployment_obs_backend_kinds_health_2026_07_09.md]
created: "2026-07-09"
last_updated: "2026-07-09"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
assigned_role: ui-developer
drift_direction: advance-code
depends_on: [deployment_obs_backend_kinds_health_2026_07_09]
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_observability_expansion_2026_07_08.md
---

# Deployment observability — kind badges, composite health, resource columns + detail popover (UI)

> **AO-DISPATCHED UI plan — starts `draft` (NOT ingested).** Released to `active` by the LAST task of the backend plan
> **`deployment_obs_backend_kinds_health_2026_07_09.md`**, so this agent only starts once the new `DeploymentItem`
> fields (6 kinds, composite/service health, cpu/mem/disk, object-delta, console-link identity) actually exist in the
> API. Full design context + the committed/mock visual contract live in the LOCAL parent
> **`deployment_observability_expansion_2026_07_08.md`** (read "Where we are" + WS-C + WS-D first). **UI gate:** no tick
> without `[UI]` + `pw:L2 ✓` + a cited regression spec (`codex/06-coding-standards/ui-testing-layers.md`); Python tools
> are banned in this repo (tsc/ESLint/Vitest/Playwright only).

## Todos

- [ ] [UI] P1. **Kind badges + rich fields** — render the 6 kinds (VM · CLOUD_RUN_JOB · CLOUD_RUN_SERVICE · ECS_SERVICE
      · LAMBDA · CLOUD_FUNCTION) and wire the mock's rich fields (machine/zone, cost, uptime) to the real API. Services
      show Mode="—". `pw:L2` regression on the kind-badge + Mode="—" render.
- [ ] [UI] P1. **Composite Health column** — chip text = exact state (7-state VM: working/stalled/oom-risk/
      workload-dead/disk-full/hung/dead; service: serving/scaled-to-zero/dead/degraded), colour = 3-tier severity
      (green=working·serving / amber=stalled·oom-risk·disk-full·degraded / red=workload-dead·hung·dead). `pw:L2`
      asserting the colour tier per state.
- [ ] [UI] P1. **Resources columns** — wire cpu/mem/disk % to the real API fields (currently mock), colour-coded (amber
      ≥70, red ≥90, `↑` on climbing mem); services show cpu/mem only, jobs none, no-sample rows show "—". `pw:L2` on the
      threshold colouring + honest "—".
- [ ] [UI] P1. **Name-click detail popover** (right-side panel) — clicking the target NAME opens a popover with the deep
      fields (cpu/mem/disk sparklines + timeline, req/min, p99, invocations, revision, running_tasks, rows in/out/error,
      object-delta breakdown, owning consolidator, absolute used/total GB) served by `/deployments/{id}/detail`. `pw:L2`
      on open/close + a sample field.
- [ ] [UI] P1. **Console deep-link** in the popover — "Open in GCP/AWS console →" built from the target identity: GCE
      `compute/instancesDetail/zones/{zone}/instances/{name}?project=…`, EC2 `ec2/home?region={r}#InstanceDetails:{id}`,
      plus Cloud Run service/job, ECS cluster/service, Lambda function URLs. Pure URL construction from fields already
      on the item; `pw:L2` asserting the href per kind.
- [ ] [UI] P2. **Kind filter** dropdown next to Mode/Cloud/Status (isolate services vs jobs vs VMs) — the way a user
      finds always-on services (Mode="—"). `pw:L2` on filter narrowing.

## Progress Log

- 2026-07-09 — Created `draft` from the LOCAL parent. Held until the backend plan's last task flips it `active` so the
  UI wires against a real `DeploymentItem` contract, not the local mock. The mock in
  `deployment_observability_expansion_2026_07_08.md` § "Where we are" is the visual target.
