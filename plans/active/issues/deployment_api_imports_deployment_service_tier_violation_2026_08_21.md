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

## Progress 2026-08-21 (interactive session, slot 17) — 2 of ~9 call sites fixed at the root, not worked around

Investigated live: the two files this doc originally cited (`_aws_deployments.py`, `_cloud_run_executions.py`) had
already been touched by another session by the time this session picked the doc up — neither imports
`deployment_service` at module level anymore. But `check-dependency-alignment.py --repo deployment-api --json`
(run against a FRESH `generate-derived-manifest.py`, not the stale cache — the first check this session ran
misleadingly said `aligned: true` off a stale derived-manifest) still failed identically, because the violation had
simply MOVED to two different call sites: `deployment_api/routes/deployment_freshness.py` (imports
`responsibility_for_deployment`) and `deployment_api/services/deploy_missing_launch.py` (imports `admission_blocked`
from the revocation gate).

**Root-caused both as genuinely stateless** — neither actually depends on deployment-service's runtime process:
`responsibility_for_deployment` is pure derivation over UAC types; `admission_blocked` reads a GCS marker directly
via UTL's `get_storage_client()`/`UnifiedCloudConfig`, no deployment-service call involved. Operator decision: relocate
both to `unified-trading-library` (matches the exact precedent of `deployment_registry.py`'s own Phase-9 relocation
for the same repo pair) rather than wrap them behind a new HTTP endpoint — zero network hop, zero drift risk (both
deployment-service's own internal callers and deployment-api now import the SAME source).

**Shipped**: `unified-trading-library@88e3fda87e` (new `deployment_shard_responsibility.py` +
`deployment_admission_gate.py` modules + tests), `deployment-service@2a9f9b379d` (both call sites +
`monitored_services.py` + `revocation_actuator.py`'s `hold_marker_path` now import from UTL;
`revocation_gate.py` trimmed to drain-side only), `deployment-service@765d174035` (deleted the now-fully-relocated
`deployment_cluster_registry.py`), `deployment-api@2d117da625` (both call sites converted; the
`deployment_cluster_registry`/`revocation_gate` dynamic-file-loading mock shims in `tests/unit/conftest.py` removed —
a MINIMAL `deployment_service`/`data_pipeline_monitors` namespace stub was restored after removal broke
`test_route_deployments_inventory_aws.py`'s own unrelated namespace-repair helper, see Progress Log). All 3 repos'
`quality-gates.sh` green before each ship.

**Re-verified live, NOT yet `aligned: true`** — `check-dependency-alignment.py --repo deployment-api --json` now
reports exactly 2 issues (down from 1, but a different 1 — see below):

```json
{"aligned": false, "issues": [
  {"repo": "deployment-api", "type": "internal_in_manifest_not_pyproject", "dep": "deployment-service"},
  {"repo": "deployment-api", "type": "external_version_mismatch", "dep": "pip", "pyproject_spec": "pip>=26.1.2", "canonical_spec": "pip>=26.2"}
]}
```

**Why `internal_in_manifest_not_pyproject: deployment-service` still fires** — two independent reasons, both
unaddressed by this session's fix:

1. `workspace-manifest.json`'s own `deployment-api.dependencies` array still lists `deployment-service` as a
   required dep (added by `e9b9ff3b65`, "canonical dep alignment 51→0" — predates this doc, not touched this
   session) — this itself needs correcting (remove the entry) once NOTHING imports deployment_service anymore.
2. **7 more files still genuinely import `deployment_service.*` directly** (confirmed via a live grep, excluding the
   sanctioned `deployment_service_client` HTTP-client abstraction, which is NOT a violation):
   - `deployment_api/routes/_cloud_run_executions.py:130,203` — `deployment_service.backends._gcp_sdk` /
     `deployment_service.backends` (multiple names)
   - `deployment_api/routes/_gcp_cloud_functions.py:95` — `deployment_service.backends._gcp_sdk`
   - `deployment_api/routes/_cloud_run_services.py:124` — `deployment_service.backends._gcp_sdk`
   - `deployment_api/services/artifact_pipeline/providers.py:442` — `deployment_service.backends._gcp_sdk`
   - `deployment_api/routes/_aws_deployments.py:69,432` — `deployment_service.backends.aws_census`
   - `deployment_api/routes/_aws_deployments.py:162` — `deployment_service.data_pipeline_monitors._gcs_tail`
   - `deployment_api/routes/vm_admin.py:262` — `deployment_service.data_pipeline_monitors.launcher_registry`
   - `deployment_api/routes/data_status/_deploy_turbo.py:606` — `deployment_service.cli.utils.manifest_reader`

   All 7 are `# noqa: imports-inside-functions`-annotated (lazy, inside function bodies) — the same signal the
   original finding noted: whoever wrote them knew these were non-standard, just not that they cross a forbidden
   tier boundary. `_gcp_sdk` is the single highest-leverage one (5 of the 7 sites) — worth investigating first
   whether it, like the two already fixed, is genuinely stateless (a thin wrapper around `boto3`/`google-cloud-sdk`
   calls with no deployment-service state) and can relocate to UTL the same way, vs. genuinely needing
   deployment-service's own cloud credentials/context and requiring the HTTP-client-wrap approach instead.

**The `pip>=26.1.2` vs `pip>=26.2` mismatch is UNRELATED** — this is the PYSEC-2026-3721/CVE-2026-13346 finding
already tracked in `cve_affected_pinned_deps_remediation_2026_06_18.md`'s "NEW 2026-08-21" section (surfaced by a
DIFFERENT escalation, `agt-614918`); not this doc's scope, not touched here, cross-referenced only.

## Todos

- [x] [BACKEND] P1. **PARTIAL — 2 of 9 call sites fixed at the root.** Restructured
      `deployment_freshness.py`'s and `deploy_missing_launch.py`'s direct `deployment_service` imports by relocating
      the two functions they needed to UTL (both genuinely stateless) — see Progress section above for full
      evidence. The doc's original two named files (`_aws_deployments.py`, `_cloud_run_executions.py`) had already
      moved their SPECIFIC violation elsewhere by the time this session found them; both still have OTHER, unfixed
      `deployment_service.backends`/`data_pipeline_monitors` imports (see the 7-file list above).
- [ ] [BACKEND] P2. Fix the 7 remaining call sites (5 `_gcp_sdk`, 1 `aws_census` x2-sites, 1 `_gcs_tail`, 1
      `launcher_registry`, 1 `manifest_reader` — see Progress section above for exact file:line). For each,
      determine whether it's genuinely stateless like the two already fixed (relocate to UTL, no new dependency) or
      genuinely needs deployment-service's own runtime/credentials (wrap behind `deployment_service_client.py`'s
      existing async-HTTP pattern instead). `_gcp_sdk` (5 of 7 sites) is the highest-leverage one to investigate
      first. Repo: deployment-api (+ deployment-service if anything needs a new API endpoint).
- [ ] [SCRIPT] P2. Once ALL `deployment_service.*` imports are gone from deployment-api, remove the stale
      `deployment-service` entry from `workspace-manifest.json`'s `deployment-api.dependencies` array (added by
      `e9b9ff3b65`, predates this doc) — re-run `check-dependency-alignment.py --repo deployment-api --json` and
      confirm `aligned: true` for real this time. Repo: unified-trading-pm.
- [ ] [AGENT] P3. Once aligned, re-run a real PM quickmerge (not just the diagnostic) to confirm Stage 1.5 passes
      again fleet-wide, not just for deployment-api specifically.

## Progress Log

- **2026-08-21 (slot 17, interactive)**: shipped the 2-function UTL relocation (see Progress section above).
  Process note: removing conftest.py's `deployment_cluster_registry`/`revocation_gate` mock shims initially broke
  `test_route_deployments_inventory_aws.py`'s OWN, unrelated namespace-repair helper — that test's helper relied on
  a `sys.modules["deployment_service.data_pipeline_monitors"]` stub (created by the SAME conftest block for a
  different reason) to short-circuit a real import of `data_pipeline_monitors/__init__.py`, which transitively pulls
  in `escalation` → `revocation_actuator` → `scripts.recovery._durable_state` (unresolvable from deployment-api's
  sys.path). Caught via `quickmerge`'s internal re-gate (a standalone `quality-gates.sh` run had NOT caught it —
  worth noting that discrepancy for whoever investigates it next, not chased further here). Fixed by restoring a
  MINIMAL empty-stub version of just that protection, without the admission-specific fakes.
