---
doc_type: issue
title: "agent-orchestrator's Cloud Run Dockerfile has a broken COPY step — references agents/, deleted 2026-07-10"
summary: >-
  Found while designing a SEPARATE containerization effort (Phase 4 of
  agent_orchestrator_ldr_main_promotion_and_qg_hardening_2026_08_19.md, a VM-replication container for the
  EC2->IONOS migration). agent-orchestrator's root `Dockerfile` (the existing Cloud Run "stateless brain" pipeline
  from agent_orchestrator_cloud_run_deployment_2026_05_19.md) has `COPY agents/ ./agents/` at line 38 — the
  `agents/` directory does not exist in the current tree, last touched by commit 5eaea293 ("read-the-file boot
  cutover") which moved worker role-file reads to the canonical PM clone instead. A `docker build` off the
  current `live-defi-rollout` HEAD against this Dockerfile would fail at that COPY step. Not verified whether this
  pipeline is actually invoked anywhere live (the companion Cloud Run deployment's prod cutover is itself gated on
  a separate plan reaching D3, per that plan's own text) — scope here is just the broken artifact itself, not
  whether it's currently exercised.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, docker, cloud-run, build-breakage, dockerfile]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
  ]
created: 2026-08-19
parent_epic: orchestrator_master
priority: P2
source: >-
  Interactive session 2026-08-19, discovered by a sub-agent building a separate VM-replication containerization
  effort (Phase 4 of the plan above) who read the existing Dockerfile for style precedent and caught the stale
  COPY path; verified directly (`grep -n "COPY agents" Dockerfile` + `ls agents/` + `git log --oneline -1 --
  agents/`) before filing.
resolved_by:
locked_by:
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []

context_scope:
  [
    agent-orchestrator/Dockerfile,
    agent-orchestrator/server/prompts.py,
    /plans/archive/2026_08/agent_orchestrator_ldr_main_promotion_and_qg_hardening_2026_08_19.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /plans/archive/2026_05/agent_orchestrator_cloud_run_deployment_2026_05_19.md,
  ]
---

# agent-orchestrator's Cloud Run Dockerfile: broken `COPY agents/` step

## Evidence

```
$ grep -n "COPY agents" Dockerfile
38:COPY agents/ ./agents/

$ ls agents/
ls: agents/: No such file or directory

$ git log --oneline -1 -- agents/
5eaea293 feat(worker-lifecycle): read-the-file boot cutover + fleet-table slot-state correctness
```

`agents/` was removed from `agent-orchestrator` in the 2026-07-10 "read-the-file boot cutover" — workers now read
their role files from the canonical `unified-trading-pm` clone at runtime instead of a copy baked into the
orchestrator's own tree (`server/prompts.py`'s own docstring documents the new mechanism). The Cloud Run
`Dockerfile` was never updated to match, so `docker build .` off current `live-defi-rollout` would fail the
moment it hits line 38.

## Context — why this wasn't caught by normal CI

This Dockerfile belongs to `agent_orchestrator_cloud_run_deployment_2026_05_19.md` (archived
`plans/archive/2026_05/`), a stateless, API-only Cloud Run "brain" deployment (explicitly no tmux — workers run
elsewhere per a companion "workers on VMs" plan). Its prod cutover is gated on that companion plan reaching a
specific milestone (D3). It's unclear from this session's read whether the image actually gets built anywhere
live today (a scheduled CI job, a manual `gcloud builds submit`, or genuinely dormant since the 2026-05 plan) —
that's the open question this issue tracks, not a claim that something is actively failing in production right
now.

## Todos

- [ ] [INFRA] P2. Determine whether this Dockerfile is built anywhere live (check `.github/workflows/` /
      `cloudbuild.yaml` trigger config for what actually invokes it, and whether that trigger has run recently —
      `gcloud builds list` or the GHA run history). If it's genuinely dormant, fixing the COPY step is still
      correct hygiene but not urgent; if something DOES still build it, this may already be a live, silent CI
      failure worth escalating.
- [ ] [INFRA] P2. Fix the `COPY agents/ ./agents/` step to match the current read-the-file architecture — likely
      means removing the COPY entirely (if the container no longer needs baked-in role files at all under the new
      read-from-PM-clone model) or replacing it with whatever the container's real runtime dependency is now.
      Read `server/prompts.py`'s docstring first to understand the current mechanism before deciding.
- [ ] [DOC] P3. Once resolved, cross-check `agent_orchestrator_cloud_run_deployment_2026_05_19.md`'s own text for
      any other stale references to the pre-cutover `agents/`-in-tree model that might need the same correction.

## Progress Log

- **2026-08-19**: Filed. Discovered as a side-effect of unrelated containerization work (Phase 4 of
  `agent_orchestrator_ldr_main_promotion_and_qg_hardening_2026_08_19.md`), verified directly, scoped as its own
  issue since it's a different deployment target/plan than the work that surfaced it.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **2026-08-20**: referrer-path fixup — the AO plan above archived (`plans/archive/2026_08/`, all 5 phases done);
  `related:`/`context_scope:` repointed to its new path.
- **na-eligibility-audit 2026-08-21 (ao tranche)**: RECLASSIFY (whole-doc) — first audit pass for this doc. All 3
  open todos are fully bounded/deterministic: (1) determine whether the Dockerfile is built anywhere live (grep
  `.github/workflows/`/`cloudbuild.yaml` trigger config + check run history — a mechanical check with a factual
  answer), (2) fix the broken `COPY agents/` step per the current read-the-file architecture (read
  `server/prompts.py`'s docstring, then make the Dockerfile match — no open design call, the target architecture
  is already documented), (3) cross-check the archived deployment plan's text for the same stale reference once
  resolved (mechanical grep). No judgment/operator-gated fork anywhere in the doc. Conflict-check: grepped
  `plans/active/` for "COPY agents"/"agent_orchestrator_cloud_run_dockerfile" — zero hits outside this doc itself.
  Flipped `assigned_vm: NA → planning`, `execution_scope: local-only → orchestrator-agent`; `assigned_role: infra`
  was already correct.
