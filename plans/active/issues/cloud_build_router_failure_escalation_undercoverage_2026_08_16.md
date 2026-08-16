---
doc_type: issue
title: >-
  `cloud_build_router_failure` AO wall_type fired for only 1 of 5 repos hit by the identical UAC
  DataTypeConfig-deletion Cloud Build cascade
summary: >-
  UAC's `7aa3143e` "delete confirmed-dead DataTypeConfig" landed on `main` ~05:05Z 2026-08-16 while the matching
  consumer-side fix in `unified-trading-library` (commit `173ceeeb`, dropping the same symbol from
  `venue_config.py`) only reached `main` + published a new Docker base image at ~05:18-05:19Z. In the ~13-minute gap,
  every downstream service whose Cloud Build happened to fire pulled the stale (pre-fix) `unified-trading-library`
  base image against the already-updated UAC, and its `operability-probe` step correctly failed on
  `ImportError: cannot import name 'DataTypeConfig' from 'unified_api_contracts'` before any bad image could deploy.
  Confirmed via direct GCP Cloud Build history (region asia-northeast1, project central-element-323112) that FIVE
  repos hit this identically: `instruments-service` (build `c189cad3`, 05:16:07), `deployment-api` (`9b04e70a`,
  05:18:34), `ml-service` (`c127dfa0`, 05:19:50), `strategy-service` (`0c36dc9f`, 05:20:41), `features-service`
  (`5782608f`, 05:27:30). `GET /api/escalations/active` on the live orchestrator shows exactly ONE matching
  escalation (`agt-d078a9`, wall_type=`cloud_build_router_failure`, repo=instruments-service, dispatched to slot 13
  at 05:26:31) — the other four repos' identical failures never generated an escalation of any wall_type. A SECOND
  instruments-service Cloud Build failure (build `0b9da9b9`) fired at 05:36Z, ~16 minutes after the first, while
  `agt-d078a9` was still `status=dispatched` (not yet resolved) — the underlying condition had not self-healed by
  the time of this sweep, correcting an earlier working hypothesis in this same run that it would clear on the next
  natural promote.
status: open
nature: issue
scope: [engineer, admin]
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    agent-orchestrator,
    unified-trading-pm,
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    deployment-api,
    ml-service,
    strategy-service,
    features-service,
  ]
tags: [ci-reconcile, cloud-build, escalation-coverage, agent-orchestrator, version-coherence, wall_type]
related:
  [
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
context_scope:
  - agent-orchestrator/server/escalation.py
created: 2026-08-16
author: claude-agent
last_updated: 2026-08-16
parent_epic: infrastructure_master
priority: P1
source: ci-reconcile skill, scheduled hourly ci_reconciler dispatch agt-d02274 (slot 8)
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# `cloud_build_router_failure` escalation under-fired for a 5-repo cascade

## What happened (ground truth, verified live)

1. `unified-api-contracts` promoted a commit to `main` (~05:05:36Z) that deletes `DataTypeConfig` from
   `unified_api_contracts/__init__.py`, believing it "confirmed-dead" (commit message:
   `refactor(registry): delete confirmed-dead DataTypeConfig + passthrough re-exports`).
2. It was not fully dead: `unified-trading-library`'s `config_interface/venue_config.py` still imported it in its
   then-currently-PUBLISHED Docker base image (though its own `live-defi-rollout` source had already dropped the
   import). UTL's own fix landed on `main` at commit `173ceeeb` (05:18:19Z) and published a new base image
   (`0.87.1.dev1+g173ceeeb9`) at 05:19:22Z.
3. In the ~13-minute window between those two events, every service whose `qg-passed` → `cloud-build-router.yml` →
   Cloud Build happened to fire pulled the OLD UTL base image against the NEW UAC package, crashing at the
   `operability-probe` step (Step #7, `docker` builder) with the `ImportError`. **No bad image reached prod** — the
   probe is a pre-deploy gate and did its job.
4. Confirmed via `gcloud builds list --project=central-element-323112 --region=asia-northeast1`: 5 distinct repos'
   Cloud Builds failed on this exact ImportError in the same window — `instruments-service`, `deployment-api`,
   `ml-service`, `strategy-service`, `features-service`.
5. `GET /api/escalations/active` shows only ONE escalation for this incident class:
   `agt-d078a9` (repo=`instruments-service`, wall_type=`cloud_build_router_failure`, dispatched to slot 13 at
   05:26:31Z, still `status=dispatched` as of this sweep ~05:37Z). No escalation of any wall_type exists for
   `deployment-api`, `ml-service`, `strategy-service`, or `features-service`'s identical failures.
6. A SECOND instruments-service Cloud Build failure (`0b9da9b9-5a09-4155-961e-e194bc3a42c8`) fired at 05:36Z — the
   condition had not yet cleared by the time of this sweep, correcting this run's own earlier working hypothesis
   that it would self-heal on the affected repos' next natural promote (their `main` hasn't moved, so nothing
   re-triggers a `qg-passed` event without a genuine new commit or a route-build re-dispatch — see cloud-build-router
   comment: "repository_dispatch payloads are not replayable").

## Why this is a finding, not just "already being handled"

The single escalation that DID fire (`agt-d078a9`) proves the `cloud_build_router_failure` wall_type and its
detection path exist and work for at least one shape of trigger. The other four repos hit the byte-identical failure
signature (same ImportError, same root cause, same ~10-minute window) and generated zero escalations — meaning
whatever creates this wall_type either (a) only watches a subset of repos, (b) has a dedup/rate-limit keyed too
broadly (e.g. one escalation per incident-class rather than per-repo) that silently swallowed the other four, or (c)
only fires on a specific trigger shape that instruments-service's failure happened to match and the others didn't
(e.g. only the FIRST Cloud Build failure in some fleet-wide window, or only failures matching a specific
`_REPO_NAME`/trigger-name pattern). This is exactly the same "one true positive doesn't prove full coverage" shape as
skill class (p) — not diagnosed further here since the root cause lives in `agent-orchestrator/server/escalation.py`
(or whatever component classifies `cloud_build_router_failure` events) and deserves its own focused read, not a
guess.

## Disposition

Not fixed this pass — root-causing the classifier needs a focused read of the escalation-creation path in
`agent-orchestrator/server/` (which this sweep did not have budget to do beyond confirming the gap), and slot 13 is
already actively working the instruments-service instance of this exact incident, so duplicating effort here would
risk cross-talk. Filed as P1 (real: 4 of 5 hit prod-service repos currently have a red Cloud Build with no automated
path to attention) for either the operator or a future `/ci-reconcile` pass to root-cause the classifier.

Suggested next steps for whoever picks this up:
- Read the escalation-creation logic for `cloud_build_router_failure` (likely a webhook/watcher reacting to the
  `cloud-build-router` Slack CRITICAL post, or a Firestore/DB write path — not yet located this pass) and determine
  why only instruments-service's event produced a row.
- Once root-caused, decide whether the other 4 repos need a manually-filed escalation now (their Cloud Builds won't
  self-clear without a fresh `qg-passed` event) or whether they're low-priority enough to wait for their next natural
  commit.

## Progress Log

- 2026-08-16 ~05:40Z: Filed by `ci_reconciler` (agt-d02274, slot 8) during the hourly sweep, after confirming via
  direct `gcloud builds list` + `GET /api/escalations/active` that 4 of 5 identically-failed repos have no
  escalation coverage. Did not attempt a root-cause fix this pass — out of scope for a quick classifier bug and a
  peer slot (13) is already actively assigned to the one repo that DID escalate.
