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

**Scope clarification, measured 2026-08-22 — this is a GOVERNANCE block, not a production incident.** The direct
imports resolve fine at runtime: deployment-api builds `FROM` the UTL base image (Dockerfile:68) and pip-installs
deployment-service `--no-deps` on top (Dockerfile:140-142), and UTL's base already supplies `boto3`, `pandas`,
`pyarrow`, `google-cloud-run`, `google-cloud-compute`. `uts-shared-deployment-api` `/health` returns 200 healthy.
Nothing is degraded for users *because of the tier violation*. Re-verified the same day:
`check-dependency-alignment.py --repo deployment-api --json` -> `aligned: false`
(`internal_in_manifest_not_pyproject: deployment-service`), so the Stage 1.5 shipping block IS still live. Urgency is
therefore pipeline-throughput, not incident — which is what justifies shipping the four relocations one at a time
with gates green between each rather than rushing them as a batch.

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
- [ ] [BACKEND] P2. **RE-DESIGNED 2026-08-22 (slot-30, interactive) — the 2026-08-21 HTTP-endpoint design is
      SUPERSEDED.** That design said "build real new deployment-service API endpoints ... matching the exact
      existing `get_cloud_run_status_batch`/`POST /api/v1/cloud-run/status-batch` pattern". Two things were wrong
      with its premises, both measured this session:
      (a) it cited `QUALITY_GATE_BYPASS_AUDIT.md` §2.5/§2.18 as "explicitly-documented, audited exceptions" for
      `_gcp_sdk` and `manifest_reader`. §2.5 is *"Imports Inside Functions — MIGRATION_PENDING"* — a different gate,
      about deployment-api's own lazy-import placement — and there is **no §2.18 in that file at all**. Neither is
      an audited exception to the tier boundary.
      (b) all four remaining modules are **stateless** — none needs deployment-service's runtime process,
      credentials, or state — so none of them warrants a network hop. Verified by import-list inspection:
      `manifest_reader` imports only UAC + UTL + pandas/pyarrow; `aws_census` only boto3 + stdlib;
      `launcher_registry` only `pathlib.Path`; `_gcp_sdk` is a 71-line lazy `__getattr__` shim with no logic.
      **Operator decision 2026-08-22: relocate to UTL, do not build HTTP endpoints.** This matches the tier
      checker's own remedy ("move shared code to a lower tier") and the 4-for-4 precedent in this repo pair
      (`deployment_shard_responsibility.py`, `deployment_admission_gate.py`, `deployment_gcs_tail.py`,
      `deployment_registry.py` all already relocated to UTL for exactly this reason). Subprocess was explicitly
      REJECTED as a fix for these: it satisfies the import-based checker while leaving the vendored-image coupling
      fully intact, and pays interpreter cold-start on per-request read paths.

      **Blast radius, measured — the four are NOT uniform; ship them one at a time, gates green in BOTH repos
      between each. Batching them is where this goes wrong.**

      | Module | consumers in deployment-service | other repos | shape |
      | --- | --- | --- | --- |
      | `aws_census` | 1 src + 2 tests | none | clean move |
      | `manifest_reader` | 4 src + 1 test | none | move, medium |
      | `launcher_registry` | 7 src + 6 tests + a dedicated QG | none | **partial** move only |
      | `_gcp_sdk` | 8 src + 1 test | none | **do not move** |

      Apparent alerting-service / agent-orchestrator hits are **string references, not imports** (log/context text
      like `launcher=(resolve via launcher_registry)`, and a docstring citation) — verified, no cross-repo import
      risk from those.

      - [x] `_gcs_tail` (`_aws_deployments.py:162`, `read_terminal_exit_code`) — DONE 2026-08-21. Relocated a
            self-contained copy of `read_terminal_exit_code`/`read_text_tail`/`_call_with_timeout`/
            `EXIT_STATUS_BLOB`/`RUN_LOG_BLOB` to a new `unified_trading_library/deployment_gcs_tail.py` module.
            Shipped: `unified-trading-library@b565fcb9fa`, `deployment-api@f0f2681876`. Both repos'
            `quality-gates.sh` green before ship.
      - [ ] **(1st — lowest risk)** `aws_census` (`_aws_deployments.py:69,432`) — relocate the whole module to
            UTL. Zero `deployment_service.*` imports; UTL already carries `boto3>=1.40.70` and has
            `cloud_interface/providers/aws.py` + `aws_compute.py` + `_aws_sdk_protocols.py` as its home. Only ONE
            deployment-service consumer to re-point (`data_pipeline_monitors/missing_live_producer_watcher.py`)
            plus its 2 tests. Preserve the `importlib.util.find_spec` degrade-to-`[]` guard verbatim.
      - [ ] **(2nd)** `_gcp_sdk` cluster (5 call sites: `_cloud_run_executions.py:132,207`,
            `_gcp_cloud_functions.py:97`, `_cloud_run_services.py:126`, `artifact_pipeline/providers.py:448`) —
            **do NOT move deployment-service's `_gcp_sdk`**; it has 8 internal consumers there and moving it buys
            that repo nothing. UTL is ALREADY a sanctioned GCP SDK boundary
            (`cloud_interface/providers/gcp_compute.py` already imports `run_v2` + `compute_v1` and wraps
            `run_v2.ServicesClient`/`RevisionsClient`). Extend UTL's `cloud_interface` with what the 5 sites need
            and point them there; leave deployment-service untouched. **One dep gap**: UTL's pyproject has
            `google-cloud-run` and `google-cloud-compute` but NOT `google-cloud-functions`, needed for the
            `functions_v2` site — add it. (It resolves in the deployed image today via the UTL base image chain,
            but it is undeclared in both lockfiles, so declare it rather than rely on that.)
      - [ ] **(3rd)** `manifest_reader` (`_deploy_turbo.py:606`, `ManifestReader.get_coverage_summary`) —
            relocate to UTL. 929 lines, zero `deployment_service.*` imports; UTL already carries pandas>=2.3 +
            pyarrow>=23 and has no `ManifestReader` name collision. FOUR deployment-service consumers to re-point:
            `cli/utils/data_status_extended.py`, `cli/commands/deploy_missing.py`, `cli/commands/data_status.py`,
            `api/routes/state.py`. Before moving, check overlap against UTL's existing manifest modules
            (`manifest_freshness.py`, `manifest_reprocess.py`, `candidate_manifest_store.py`) so this does not
            become a 5th parallel manifest reader.
      - [ ] **(4th — PARTIAL move, read the gotcha)** `launcher_registry` (`vm_admin.py:262`) — move ONLY the
            `LAUNCHER_FOR_VM_PREFIX` dict + `resolve_launcher_for_vm()` + `is_known_non_capture_host()` to UTL.
            **Leave `_LAUNCHER_DIR` and `launcher_path()` in deployment-service.** Why: `launcher_registry.py:59`
            is `_LAUNCHER_DIR = Path(__file__).resolve().parents[2] / "scripts" / "vm"` — move that file into UTL
            and `parents[2]` resolves inside UTL's tree, where `scripts/vm/launch-*.sh` does not exist, so
            `launcher_path()` returns a bogus path **with no exception raised**. Its guard gate
            (`scripts/quality_gates/check_vm_launcher_prefix_registration.py`) also walks deployment-service's own
            `scripts/vm/` and documents itself as repo-local. deployment-api imports only
            `resolve_launcher_for_vm` and never calls `launcher_path()` — verified — so the partial move is
            sufficient for it.
      - [ ] Once every site above is converted, re-run `check-dependency-alignment.py --repo deployment-api
            --json` and confirm `aligned: true`.
- [ ] [SCRIPT] P2. Once ALL `deployment_service.*` imports are gone from deployment-api, remove the stale
      `deployment-service` entry from `workspace-manifest.json`'s `deployment-api.dependencies` array (added by
      `e9b9ff3b65`, predates this doc) — re-run `check-dependency-alignment.py --repo deployment-api --json` and
      confirm `aligned: true` for real this time. Repo: unified-trading-pm.
- [ ] [AGENT] P3. Once aligned, re-run a real PM quickmerge (not just the diagnostic) to confirm Stage 1.5 passes
      again fleet-wide, not just for deployment-api specifically.
- [ ] [OPERATOR] P2. **Unrelated live defect found in passing 2026-08-22, filed here per the same
      cross-reference convention this doc already uses for the `pip` mismatch.** The GCP Cloud Functions inventory
      panel has been silently empty in prod: `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` lacks
      `cloudfunctions.functions.list`. Confirmed from Cloud Run logs, not inferred —
      `GCP Cloud Functions census failed (degrading to empty list): 403 Permission 'cloudfunctions.functions.list'
      denied on 'projects/central-element-323112/locations/asia-northeast1/functions'` (2026-08-21T12:21:22Z and
      :17Z). `deployment_api/routes/_gcp_cloud_functions.py:123`'s `except Exception` degrades this to `{}` by
      design, so the panel shows empty rather than erroring and nobody notices. Fix is an IAM grant
      (`roles/cloudfunctions.viewer` on the project, or the narrower list permission) — per CLAUDE.md both cloud
      identities are IAM-self-service, so this is a fix, not an ask. Tagged `[OPERATOR]` because it is a
      **production IAM change**, not because it is blocked. Repos: none (infra). NOTE: while fixing, consider
      whether "degrade to empty" is the right contract for a *permission* error as opposed to a transient API
      error — a permanently-empty panel that never alerts is how this survived undetected.

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
- **2026-08-22 (slot-30, interactive)**: P2's HTTP-endpoint design SUPERSEDED and replaced with a measured
  UTL-relocation design (see the todo). Corrections made this session, each verified rather than reasoned:
  (1) the `QUALITY_GATE_BYPASS_AUDIT.md` §2.5/§2.18 citation does not support the tier-boundary exception it was
  cited for — §2.5 is a different gate (imports-inside-functions) and §2.18 does not exist;
  (2) all four remaining modules are stateless (import lists inspected), so none needs a network hop;
  (3) inbound blast radius measured per module (1 / 4 / 7 / 8 deployment-service consumers) — the four are not
  interchangeable and `launcher_registry` would break SILENTLY if moved whole, via its `parents[2]`-rooted
  `_LAUNCHER_DIR`;
  (4) `_gcp_sdk` should not move at all — UTL is already a GCP SDK boundary and deployment-service has 8 internal
  consumers;
  (5) the tier violation is a governance/pipeline block, not a runtime break — the deployed image resolves the
  imports fine.
  Also corrected the root-cause claim in the sibling issue
  `/plans/active/issues/deployment_service_client_broken_functions_2026_08_20.md` and at its origin in
  `deployment-api/deployment_api/clients/deployment_service_client.py`'s docstring: deployment-service's API IS
  deployed (Cloud Run `deployment-dashboard`, all 13 `/api/v1` routes, publicly invokable, HTTP 200 measured) —
  the nine "broken HTTP functions" are broken only because `DEPLOYMENT_SERVICE_URL` is never set. That false claim
  had already misdirected at least one downstream session into designing endpoints against a server it believed
  absent. No code changes to the four call sites yet — corrections and design only.
