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
- [ ] [BACKEND] P2. **Fully scoped 2026-08-21 (interactive session, slot 17) — ready to implement, see the
      Progress section below for the concrete per-item design.** All 7 remaining call sites investigated;
      NONE are simple relocations like the first two (both `_gcp_sdk.py` and `cli/utils/manifest_reader.py` turn
      out to be **explicitly-documented, audited exceptions** in `QUALITY_GATE_BYPASS_AUDIT.md` §2.5/§2.18 with
      their own stated resolution paths — not oversights — and `launcher_registry`'s 400-line dict is guard-tested
      against deployment-service's own file tree, a poor relocation candidate). Operator decision 2026-08-21:
      build real new deployment-service API endpoints for the genuinely-live/credentialed pieces, matching the
      exact existing `get_cloud_run_status_batch`/`POST /api/v1/cloud-run/status-batch` pattern in
      `deployment_service_client.py`, rather than relocating or overriding the documented exceptions. Execute
      each item below one at a time — design, implement, `quality-gates.sh` green in both repos, ship via
      quickmerge, flip this todo's checklist — same rigor as the two already-shipped fixes. Repo: deployment-api +
      deployment-service.
      - [x] `_gcs_tail` (`_aws_deployments.py:162`, `read_terminal_exit_code`) — DONE 2026-08-21. Relocated a
            self-contained copy of `read_terminal_exit_code`/`read_text_tail`/`_call_with_timeout`/
            `EXIT_STATUS_BLOB`/`RUN_LOG_BLOB` to a new `unified_trading_library/deployment_gcs_tail.py` module
            (deliberately NOT importing deployment-service's own `_gcs.py`/`_gcs_tail.py` back out, per the
            original design note — `_gcs.py` has 5 other internal deployment-service-only consumers not worth
            the blast radius). Bare `except Exception:` sites converted to `except Exception as exc: logger.debug(...)`
            to match `deployment_admission_gate.py`'s sibling convention and clear UTL's broad-except gate.
            Shipped: `unified-trading-library@b565fcb9fa` (module + `__init__.py` export + 7 unit tests, mirrors
            deployment-service's own `test_gcs_tail.py` coverage), `deployment-api@f0f2681876` (`_aws_deployments.py`
            call site swapped to `from unified_trading_library import read_terminal_exit_code`). Both repos'
            `quality-gates.sh` green before ship. Re-verified: `check-dependency-alignment.py --repo deployment-api
            --json` still `aligned: false` (expected — 6 call sites remain of the original 7).
      - [ ] `manifest_reader` (`_deploy_turbo.py:606`, `ManifestReader.get_coverage_summary`) — **no new endpoint
            needed.** deployment-service already exposes `GET /api/v1/data-coverage-summary`
            (`deployment_service/api/routes/state.py:592`) wrapping the exact same call
            (`ManifestReader.get_coverage_summary(service, asset_groups)`). Add a `get_data_coverage_summary`
            async client method to `deployment_service_client.py` (mirror `get_cloud_run_status_batch`'s
            shape) and swap `_deploy_turbo.py`'s import for a client call — the route is already `async def`
            with `await asyncio.to_thread(...)`, so this is a straight swap, no async-conversion needed.
      - [ ] `launcher_registry` (`vm_admin.py:262`, `resolve_launcher_for_vm`) — add a tiny new
            `GET /api/v1/vm/{vm_name}/launcher` deployment-service endpoint (returns `{launcher: str|null}`) +
            matching client method; convert `vm_admin.py`'s restart-decision route to call it instead of
            importing the registry directly.
      - [ ] `_gcp_sdk` cluster (4 files, 5 operations — the biggest piece): add new deployment-service endpoints
            for each, following `get_cloud_run_status_batch`'s exact request/response shape convention:
            - `list_cloud_functions(project_id, region)` (`_gcp_cloud_functions.py:95`) → new endpoint
            - `list_cloud_run_services(project_id, region)` (`_cloud_run_services.py:124`) → new endpoint
            - `latest_execution_by_job(project_id, region)` (`_cloud_run_executions.py:130`) → new endpoint
            - `list_job_executions(project_id, job_short_name, region, limit)` (`_cloud_run_executions.py:203`)
            → new endpoint (detail-popover run-history, page_size=limit vs the thin-list's page_size=1 —
            keep this cost distinction in the new design)
            - `gcp_cloud_run_revisions(cfg)` (`artifact_pipeline/providers.py:442`) — reuses
            `list_cloud_run_services` internally + lists revisions per service (`RevisionsClient`); design
            as its own endpoint or fold into the cloud-run-services response, whichever avoids a second
            services-list RPC (the existing code deliberately reuses one list to avoid exactly that)
            Each of the 4 deployment-api call sites converts from its current sync function (some already
            called from async routes via a sync boundary) to an async client call — verify each call site's
            actual caller context before converting, since `providers.py`'s usage may differ from the route
            files'. Preserve the "honest degradation to `[]`/`{}` on any error, never a crash" contract exactly
            — every existing function already documents this as deliberate.
      - [ ] `aws_census` (`_aws_deployments.py:69,432` — `list_batch_census`/`list_ec2_census`/
            `list_ecs_census`/`list_lambda_census`): add ONE combined new deployment-service endpoint
            returning all 4 census types together (matches how `_aws_deployments.py`'s own `load_aws_inventory`
            already calls all 4 together for one inventory build — no reason to split into 4 round-trips).
            Preserve the existing `importlib.util.find_spec` degrade-to-`[]` guard's INTENT (the AWS census
            seam being genuinely unavailable) as an HTTP-level equivalent (a clean error response the caller
            degrades on, not a crash).
      - [ ] Once every site above is converted, re-run `check-dependency-alignment.py --repo deployment-api
            --json` and confirm `aligned: true`.
- [ ] [SCRIPT] P2. Once ALL `deployment_service.*` imports are gone from deployment-api, remove the stale
      `deployment-service` entry from `workspace-manifest.json`'s `deployment-api.dependencies` array (added by
      `e9b9ff3b65`, predates this doc) — re-run `check-dependency-alignment.py --repo deployment-api --json` and
      confirm `aligned: true` for real this time. Repo: unified-trading-pm.
- [ ] [AGENT] P3. Once aligned, re-run a real PM quickmerge (not just the diagnostic) to confirm Stage 1.5 passes
      again fleet-wide, not just for deployment-api specifically.

## Progress Log

- **2026-08-21 (slot 17, interactive), later same session**: fully scoped the remaining 7 call sites (design
  above) — no code changes yet, investigation + design only. Also verified live: every repo in slot 17 clean +
  `ahead=0 behind=0` against `origin/live-defi-rollout` (pulled `unified-trading-pm` 16 commits forward — was
  behind), `unified-trading-ci` confirmed clean on its own `main` branch (exempt from the LDR-alignment check).
  Confirmed no other session had landed any of these 7 fixes in the interim (fresh grep post-pull, same counts).
- **2026-08-21 (slot 17, interactive)**: shipped the 2-function UTL relocation (see Progress section above).
  Process note: removing conftest.py's `deployment_cluster_registry`/`revocation_gate` mock shims initially broke
  `test_route_deployments_inventory_aws.py`'s OWN, unrelated namespace-repair helper — that test's helper relied on
  a `sys.modules["deployment_service.data_pipeline_monitors"]` stub (created by the SAME conftest block for a
  different reason) to short-circuit a real import of `data_pipeline_monitors/__init__.py`, which transitively pulls
  in `escalation` → `revocation_actuator` → `scripts.recovery._durable_state` (unresolvable from deployment-api's
  sys.path). Caught via `quickmerge`'s internal re-gate (a standalone `quality-gates.sh` run had NOT caught it —
  worth noting that discrepancy for whoever investigates it next, not chased further here). Fixed by restoring a
  MINIMAL empty-stub version of just that protection, without the admission-specific fakes.
