---
doc_type: issue
title: deployment-api directly imports deployment-service modules — violates the documented service-boundary, blocks PM's Stage 1.5 dependency-alignment gate fleet-wide
summary: >-
  Found 2026-08-21 while shipping unrelated T4-tranche docs: `unified-trading-pm`'s quickmerge Stage 1.5
  ("Dependency Alignment") fails with `internal_in_manifest_not_pyproject: deployment-service` for repo
  `deployment-api`. Root cause: `deployment_api/routes/_aws_deployments.py` and
  `deployment_api/routes/_cloud_run_executions.py` both do `from deployment_service.backends... import ...` —
  real, live imports of `deployment-service` Python modules — despite `deployment-api`'s OWN codebase explicitly
  documenting this boundary as forbidden: `deployment_api/clients/deployment_service_client.py`'s module
  docstring states "deployment-api must NOT import deployment-service Python modules directly", and
  `deployment_api/config_loader.py`/`deployment_api_config.py` say the same. `scripts/manifest/generate-derived-manifest.py`
  correctly derives `deployment-service` as an internal dependency of `deployment-api` from these real imports, but
  `deployment-api/pyproject.toml` has no such dependency declared (correctly, per the tier DAG — adding it would be
  the wrong fix, since deployment-api sits at a tier that must not depend on deployment-service). Running
  `scripts/manifest/fix-internal-dependency-alignment.py --apply` confirms this: it refuses to auto-add the pyproject
  entry, printing `TIER_VIOLATION (architectural change required): [deployment-api] imports [deployment-service] —
  add_to_pyproject would violate tier DAG. Fix: move shared code to a lower tier, or restructure dependency.`
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [tier-violation, dependency-alignment, deployment-api, deployment-service, quickmerge, fleet-blocking]
related:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-21
priority: P1
parent_epic: ci_master
source: >-
  Discovered incidentally while shipping unrelated T4-tranche codex/epic doc corrections via
  code_readiness_t4_execution_settlement_2026_08_19.md's autonomous session — quickmerge's Stage 1.5 blocked the
  ship, forcing investigation. Not this tranche's repos to fix; filed rather than silently worked around.
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
sequential: false
context_scope: [/codex/04-architecture/tier-and-import-architecture.md]
---

# deployment-api directly imports deployment-service modules — tier violation, blocks PM's Stage 1.5 gate fleet-wide

## Impact

**Every `unified-trading-pm` quickmerge fails at Stage 1.5 (Dependency Alignment) right now**, regardless of what
files a session is actually shipping — confirmed via direct diagnostic
(`python3 scripts/manifest/check-dependency-alignment.py --json`), not just the quickmerge log. Sessions can work
around it with a direct push under the `dirty-deps` carve-out (CLAUDE.md git-discipline HARD RULE), but that carve-out
exists for exactly this kind of pre-existing, unrelated blocker — it should not become the routine path for PM ships.

## Root cause

`deployment_api/routes/_aws_deployments.py` and `deployment_api/routes/_cloud_run_executions.py` both import
`deployment_service.backends.*` / `deployment_service.data_pipeline_monitors.*` directly (confirmed via grep,
multiple call sites in each file, including some already `# noqa: imports-inside-functions`-annotated — meaning
whoever wrote them was aware these are non-standard imports, just not that they cross a forbidden tier boundary).
This directly contradicts the SAME repo's own documented boundary:

- `deployment_api/clients/deployment_service_client.py` docstring: "deployment-api must NOT import deployment-service
  Python modules directly."
- `deployment_api/deployment_api_config.py`: "...import deployment-service as a Python package; interaction is via
  messaging/APIs/storage."
- `deployment_api/config_loader.py`: "...import boundary with deployment-service. deployment-api must not import..."

So a client/config abstraction already exists specifically to avoid this — `_aws_deployments.py`/
`_cloud_run_executions.py` bypass it.

## Todos

- [ ] [BACKEND] P1. Restructure `_aws_deployments.py`'s and `_cloud_run_executions.py`'s direct
      `deployment_service.backends`/`deployment_service.data_pipeline_monitors` imports to go through the existing
      `deployment_service_client.py` abstraction (or messaging/API/storage per its own docstring) instead — the
      abstraction layer this repo already built for exactly this boundary. Confirm no functional behavior change
      (these are backend census/log-tailing calls — trace what data crosses the boundary before restructuring).
- [ ] [AGENT] P2. Once fixed, re-run `python3 scripts/manifest/check-dependency-alignment.py --json` and confirm
      `aligned: true`; re-run a real PM quickmerge (not just the diagnostic) to confirm Stage 1.5 passes again.
