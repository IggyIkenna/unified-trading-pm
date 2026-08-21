---
doc_type: issue
title:
  deployment-api -> deployment-service tier violation blocks unified-trading-pm's dependency-alignment gate
  fleet-wide
summary: >-
  quickmerge's STAGE 1.5 Dependency Alignment check fails for every unified-trading-pm shipment right now because
  deployment-api's code imports deployment-service in a way that violates the tier DAG (no repo may import a
  higher-or-equal tier), and fix-internal-dependency-alignment.py explicitly declines to auto-fix a
  TIER_VIOLATION. Blocks ALL PM ships until resolved -- not caused by, or fixable within, any one PM commit.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-api, deployment-service]
scope: [engineer, admin]
tags: [dependency-alignment, tier-violation, quickmerge, ci-cd]
related:
  [
    /plans/active/issues/deployment_service_client_broken_functions_2026_08_20.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-21
author: agent
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source: [interactive session slot 14, 2026-08-21 -- hit while shipping an unrelated PM P1 via quickmerge]
resolved_by:
locked_by:
context_scope:
  [
    scripts/manifest/fix-internal-dependency-alignment.py,
    scripts/manifest/README-DEPENDENCY-ALIGNMENT.md,
    /plans/active/issues/deployment_service_client_broken_functions_2026_08_20.md,
  ]
---

# deployment-api -> deployment-service tier violation blocks the PM dependency-alignment gate

## What I found

`bash scripts/quickmerge.sh ... --agent --files ...` for unified-trading-pm fails at STAGE 1.5 (Dependency
Alignment) for EVERY commit right now, not just mine -- confirmed across 3 separate retries spanning ~12 commits
of branch churn, identical failure each time:

```
[unified-trading-pm] ❌ Dependency alignment FAILED
```

`python3 scripts/manifest/check-dependency-alignment.py --json`:

```json
{
  "aligned": false,
  "issues": [{ "repo": "deployment-api", "type": "internal_in_manifest_not_pyproject", "dep": "deployment-service" }],
  "count": 1
}
```

The documented remediation (`fix-internal-dependency-alignment.py --apply`) explicitly DECLINES to auto-fix this
one:

```
TIER_VIOLATION (architectural change required):
  [deployment-api] imports [deployment-service] — add_to_pyproject would violate tier DAG
  Fix: move shared code to a lower tier, or restructure dependency.
  Continuing to apply non-violation fixes...
Planned 0 action(s)
```

## Why it matters

STAGE 1.5 is unconditional for every unified-trading-pm quickmerge -- this blocks ALL PM shipments (docs, plans,
scripts) fleet-wide until resolved, regardless of what the individual commit touches. Confirmed unrelated to my
own diff (a bare-root dirty-alert watchdog + a pkill-guard fix -- no dependency/manifest/pyproject files touched
by either).

`deployment-api` already has a documented, live HTTP-client relationship with `deployment-service` (see related
doc: `deployment_service_client.py`) -- this tier violation is a static PACKAGE-DEPENDENCY-level artifact, not
evidence the services shouldn't talk to each other at the HTTP level. Needs someone who owns
deployment-api/deployment-service tiering to decide the right fix -- not attempted here (genuinely architectural,
not a mechanical rename/import fix).

## Recommended decision

- [ ] [BACKEND] P1. Diagnose exactly which import in deployment-api's code triggers the tier-DAG violation against
      deployment-service (re-run `python3 scripts/manifest/fix-internal-dependency-alignment.py` -- it currently
      only reports the repo-level pair, not the offending file/line) then either move the shared code to a lower
      tier or restructure the import so deployment-api no longer needs deployment-service as a package
      dependency. Its existing HTTP-client pattern (`deployment_service_client.py`, per
      `deployment_service_client_broken_functions_2026_08_20.md`) may already be the intended non-import boundary
      -- check whether the flagged import is dead/incidental (e.g. a stray type-only import) before assuming a
      real architectural violation. Repo: deployment-api (+ possibly deployment-service).

## Progress Log

- 2026-08-21, slot 14: found while shipping an unrelated PM P1 via quickmerge -- every retry (3 total) hit the
  identical STAGE 1.5 failure across ~12 commits of branch churn. Declaring a `qg_red` repo-blocker for
  unified-trading-pm per RULES.md §4b rather than attempting the architectural fix myself.
