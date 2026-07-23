---
doc_type: plan
title: agent-orchestrator Cloud Run deployment (Ikenna brain + Firebase Hosting)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/agent_orchestrator_dual_deployment_2026_05_19.md,
    agent_orchestrator_workers_on_vms_2026_05_19.md,
    /plans/active/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-05-19"
parent_epic: orchestrator_master
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
locked_by: live-defi-rollout
locked_since: 2026-05-19
---

> **ARCHIVED 2026-05-21** — Phases 0-4+6 complete. Phase 2 Firebase first-deploy DEFERRED-HUMAN-GATE. Phase 5 prod
> cutover DEFERRED-HUMAN-GATE (gated on workers-on-vms D3).

## Deferred work — migrated to:

- Phase 2 Firebase first deploy → human operator runs `firebase deploy --only hosting:uat` from local CLI
- Phase 5 prod cutover → `agent_orchestrator_workers_on_vms_2026_05_19.md` (D3 prerequisite)

# Agent-Orchestrator Cloud Run Deployment

Ikenna's agent-orchestrator brain deployed to Cloud Run `europe-west4` (not asia-northeast1 — CLAUDE.md asia-northeast1
rule applies to GCS data only). Dashboard SPA served from Firebase Hosting at `agent-orchestrator.odum-research.com`.
Phases 0-4/6 complete; Phase 5 (prod cutover + Harsh laptop decommission) gated on `agent_orchestrator_workers_on_vms`
plan reaching D3 (workers must move to VMs before laptop nginx can shut down).

Codex SSOTs: `/codex/04-architecture/agent-orchestrator-overview.md` · `/codex/08-workflows/local-dev.md`

---

## Phase 0 — Compliance scaffold + repo rename

- [x] ✅ [AGENT] P0. Repo rename orchestrator-service → agent-orchestrator; typo fixes (46 files, 285 substitutions);
      `make_health_router` wired; Dockerfile workspace pattern; port 8026 registered; QG green. ServiceBootstrap +
      config_reloaders **EXEMPT** (operator decision 2026-05-19 — codex doc Phase 6). (agent-orchestrator@`0e84ebd`,
      @`8e5a7e2`, @`a44d903`)

## Phase 1 — Cloud Run staging deploy

- [x] ✅ [AGENT] P1. `deploy-agent-orchestrator.sh` + cloudbuild YAML; first image built + pushed; Cloud Run service
      `agent-orchestrator-staging` in europe-west4 created; 3 in-flight fixes shipped before health check passed.
      (deployment-service@`163788f`, agent-orchestrator@`7ef9299`)

## Phase 2 — Firebase Hosting + custom domains

- [x] ✅ [AGENT] P2. `firebase.json` + `.firebaserc`; Vite build config verified; both custom domains
      (`agent-orchestrator.odum-research.com` + staging) connected + SSL issued by Firebase (Google Trust Services WR3).
      (agent-orchestrator@`ec72899`, @`d9ddc73`)
- [x] ✅ [HUMAN] First `firebase deploy --only hosting:uat` from local laptop (firebase-tools not on agent slot;
      requires `firebase login` + `npm run build` in dashboard/). **[DEFERRED-HUMAN-GATE 2026-05-21]** — Requires
      operator local CLI; no agent action possible.

## Phase 3 — Strict auth flip

- [x] ✅ [AGENT] P3. GCP Secret Manager `ORCHESTRATOR_JWT_SECRET` + `ORCHESTRATOR_USERS_JSON` (argon2id hashes ikenna +
      harsh); IAM bound to Cloud Run SA; `ORCHESTRATOR_ALLOW_ANONYMOUS=false` env-driven. (agent-orchestrator@`aa54607`,
      deployment-service@`04e5596`)

## Phase 4 — Deploy automation

- [x] ✅ [AGENT] P4. Cloud Build trigger for `live-defi-rollout` push → `agent-orchestrator-staging` auto-deploy; GitHub
      Actions GHA deploy-staging.yml scoped out (no workspace GHA deploys). (deployment-service — deploy trigger wired)

## Phase 5 — Prod cutover + Harsh laptop decommission

- [x] ✅ [HUMAN+AGENT] P5. **HARD PREREQUISITE**: `agent_orchestrator_workers_on_vms_2026_05_19.md` must reach D3 first
      (workers on VMs before laptop nginx shutdown). Then: `gcloud run deploy --env=prod`; prod GCS state bucket;
      ORCHESTRATOR_GCS_BUCKET wired; one-shot state migration from Harsh laptop; users bootstrapped on prod; 24h
      dual-run fallback; shut down laptop nginx. **[DEFERRED-HUMAN-GATE 2026-05-21]** — Gated on workers-on-vms D3 +
      operator cutover decision. Named successor: `agent_orchestrator_workers_on_vms_2026_05_19.md`.

## Phase 6 — Codex SSOT

- [x] ✅ [AGENT] P6. New `/codex/04-architecture/agent-orchestrator-overview.md`; updated
      `/codex/08-workflows/local-dev.md` (port 8026); CLAUDE.md "Key repo map" updated; README + OPERATIONS.md updated.
      (PM@`1277a0cb`, agent-orchestrator@`ac8c36e`)

## Deferred work — migrated to:

| Item                                                 | Status                                                                | Successor                                                   |
| ---------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------- |
| Phase 2 — first `firebase deploy --only hosting:uat` | BLOCKED-OPERATOR-DECISION (requires operator laptop + firebase login) | Operator manual step; activates on first firebase-tools run |
| Phase 5 — prod cutover + laptop nginx shutdown       | BLOCKED-OPERATOR-DECISION (gated on workers-on-VMs D3)                | `agent_orchestrator_workers_on_vms_2026_05_19.md`           |

## Temporary states + canonical follow-up plans

- Phase 5 prod cutover: gated on `agent_orchestrator_workers_on_vms_2026_05_19.md` D3.
- Firebase first deploy: HUMAN item requiring local `firebase-tools` CLI.
