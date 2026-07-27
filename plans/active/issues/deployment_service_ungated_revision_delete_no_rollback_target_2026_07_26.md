---
doc_type: issue
title:
  "deploy-ui.sh / deploy-agent-orchestrator.sh route 100% traffic to the new Cloud Run revision and delete every prior
  revision with NO health check gate — a bad revision that passes build but fails at runtime has no
  instant-rollback-via-traffic-shift target"
summary: >-
  `deployment-service/scripts/cloud-run/deploy-ui.sh` (lines 155-183) and `deploy-agent-orchestrator.sh` (lines 135-157)
  both: (1) deploy the new revision, (2) `gcloud run services update-traffic --to-latest` immediately, (3) loop over
  `gcloud run revisions list` and `gcloud run revisions delete` every revision except the one just deployed — with no
  health check between steps 2 and 3. A sibling script in the same directory, `canary-deploy.sh`, does this correctly
  (canary traffic split, poll `/health` for `MONITOR_DURATION`, auto-rollback to the prior revision on failure, only
  deletes the failed revision) — proving the safe pattern already exists in this repo, just isn't used by these two.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [deployment, cloud-run, rollback, health-check, deploy-scripts]
related: []
created: 2026-07-26
priority: P2
parent_epic: infrastructure_master
source:
  ["operator question 2026-07-26: does CI/CD auto-rebuild+redeploy, and does cleanup ever leave zero rollback target"]
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
drift_direction: NA
depends_on: []
execution_scope: orchestrator-agent
---

## What I found

Both scripts hard-delete every other Cloud Run revision immediately after switching 100% traffic to the new one, with
zero health verification in between:

```bash
# deploy-ui.sh:163-165
gcloud run services update-traffic "${SERVICE}" --region "${region}" --to-latest
echo "=== Cleaning up old revisions (${region}) ==="
# ...loop deleting every revision except LATEST via `gcloud run revisions delete`
```

Same shape in `deploy-agent-orchestrator.sh:135-157`. Neither script checks `/health` / `/healthz` / `/readiness`
(agent-orchestrator's own script prints those URLs as a post-deploy _suggestion_ to the operator at line 173-175 — it
doesn't gate on them itself).

Contrast `canary-deploy.sh` in the same directory: splits traffic, polls the health endpoint for a configurable window,
and only promotes to 100% (deleting nothing but the failed candidate) if healthy — otherwise rolls back to the prior
revision at 100% traffic. The safe pattern is a proven, already-written sibling script;
`deploy-ui.sh`/`deploy-agent-orchestrator.sh` just don't call it.

**Not confirmed wired into a live automatic trigger** — grepped every `.yml`/`.yaml` workflow + Cloud Build config
across `deployment-ui/`, `agent-orchestrator/`, `deployment-service/`, and `unified-trading-pm/.github/workflows/` for
either script name and found zero references. `deployment-ui`'s actual live auto-deploy path is a native GCP Cloud Build
trigger (`deployment-ui-main-deploy`) whose `cloudbuild.yaml` has its own `gcloud run deploy` step — a different code
path from `deploy-ui.sh`. `agent-orchestrator` is confirmed running on an EC2 VM via systemd self-pull (not Cloud Run)
as of 2026-07-14, so `deploy-agent-orchestrator.sh` may be dead code from before that migration. This lowers urgency
(likely operator-invoked-manually-only, if invoked at all) but does not eliminate the risk — an operator or a future
automation hookup could still run either script and hit this.

## Why it matters

Artifact Registry itself has no cleanup policy fleet-wide (verified live, `cleanupPolicies=[]` across 20+ repos) — the
underlying image is always redeployable, so recovery is never permanently impossible. But these two scripts remove the
_instant_ rollback path (an atomic traffic-shift back to a known-good revision) for the one narrow window where it
matters most: right after a deploy, before anyone has verified the new revision is actually healthy at runtime (not just
that it built). A revision that passes `cloudbuild.yaml`'s build/test steps but crashes on boot or fails its first real
request would, under these scripts, already have zero prior revisions left to shift traffic back to — recovery becomes
"rebuild and redeploy from a known-good image tag", not "flip traffic".

## Recommended decision

- [ ] [SCRIPT] P2. Either (a) call `canary-deploy.sh`'s pattern from `deploy-ui.sh` and `deploy-agent-orchestrator.sh`
      instead of the current unconditional switch, or (b) at minimum keep the previous N (e.g. 2-3) revisions instead of
      deleting down to 1, and add a health-check gate before the traffic switch. First confirm live-wiring status (grep
      CI/CD configs + operator confirmation of whether either script is invoked anywhere, scheduled or manual) before
      prioritizing — if genuinely dead/superseded code, this may be a deletion candidate instead of a fix candidate.
      (repo: deployment-service)

## Codex SSOTs

None new — this is a script-safety gap in `deployment-service`, not an architecture or contract question.
Cross-reference: `/codex/05-infrastructure/deployment-observability.md` (if it documents the intended rollback contract,
verify these scripts against it as part of the fix).
