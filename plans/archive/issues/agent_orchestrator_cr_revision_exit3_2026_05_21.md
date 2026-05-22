---
title: "agent-orchestrator staging revision 00012 exits with code 3"
created: 2026-05-21
author: slot-8
source:
  - plans/active/agent_orchestrator_slack_notifications_2026_05_19.md
locked_by: live-defi-rollout
priority: P2
status: BLOCKED-OPERATOR
blocked_reason:
  "Operator or slot-1 must re-trigger staging deploy (deploy-agent-orchestrator.sh --env=uat --cloud) to determine if
  exit(3) is transient or recurring"
---

> **[ACKED-INTO-CODE]** Archived 2026-05-22. Root cause: `data/config/backlog.yaml` is gitignored (runtime artifact), so
> it was absent from the container image. In `ORCHESTRATOR_MODE=live`, `load_backlog()` called `path.open()` on a
> nonexistent file → `FileNotFoundError` → uvicorn lifespan startup failed → exit(3). Fix: `server/backlog.py` now
> returns empty `Backlog()` when file is absent. Revision 00014 deployed successfully, `STATUS: True`. commit `d2e8354`
> in agent-orchestrator.

## What I found

Cloud Build job `62790111` built + pushed image `:uat` successfully. `gcloud run deploy` created revision
`agent-orchestrator-staging-00012-l88`. Revision failed healthcheck with `Container called exit(3)` — container started
but exited before port 8080 became reachable.

Build was triggered by deploy script during P4 smoke test (commit `07e42e2` — async→sync Slack conversion, import
reorganisation from ruff auto-format).

Active revision `agent-orchestrator-staging-00011-mtg` unaffected (secrets mounted, smoke test passed on it with
350-460ms latency confirming Slack calls working).

Local import test passed: `python -c "import server.server; print('import OK')"` with agent-orchestrator `.venv` →
`import OK`.

## Why it matters

Prod deploy will use the same script + image. If exit(3) recurs on prod revision, prod service would be unavailable.
Current staging is fine (00011-mtg handles all traffic).

## Recommended decision

1. Check if exit(3) is transient: re-trigger deploy and observe if new revision starts OK.
2. If recurs: pull image locally and run with `docker run --env ... europe-west4-docker.pkg.dev/...` to capture Python
   traceback.
3. Possible root cause: ruff auto-format reordered `from .accounts import load_accounts` earlier in server.py — check if
   this creates circular import in the container's dependency set.
4. Fix in agent-orchestrator before prod deploy.

## Next step

Operator or slot 1 to re-trigger staging deploy:
`bash deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh --env=uat --cloud` and observe if 00013 starts
cleanly.

## Status update — 2026-05-22

**BLOCKED-OPERATOR**: Cannot re-trigger Cloud Run deployment without GCP Console/CLI access. Operator must run:

```bash
bash deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh --env=uat --cloud
```

Then check if the new revision starts cleanly (exit 0) or reproduces exit(3). If exit(3) recurs → file P0 bug in
`plans/active/` with `parent_epic: orchestrator_master`. If resolved → archive this issue as ACKED-INTO-CODE.
