---
doc_type: issue
title:
  "deployment-service's shard-storage-env resolver and two fleet sweep scripts key on the stale plural
  'execution-services', silently missing the real 'execution-service' repo/service"
summary:
  'Found while fixing infra_satellite_ao_dispatch_batch1_2026_07_26.md''s execution-service `service_name` manifest
  drift todo (repo: execution-service). That fix confirmed the canonical, workspace-wide form is singular
  ''execution-service'' (matches ManifestWriter/ServiceBootstrap/SERVICE_TO_KIND/auth.py/isolation_policy.py, and
  matches the real on-disk `configs/sharding.execution-service.yaml`, whose own `service:` field is singular). Two
  independent gaps in deployment-service still key on the plural: (1) `shard_builder.py`''s `_SERVICE_STORAGE_DOMAINS`
  dict has key ''execution-services'' -> [''execution-store''], but `build_storage_env_vars(service, ...)` (called from
  `worker_manager.py:164` and `_worker_rolling.py:160` with `state.service`, which resolves to the singular form per the
  sharding YAML) does `_SERVICE_STORAGE_DOMAINS.get(service, [])` -- a silent miss returns `[]`, meaning no
  EXECUTION_STORE_GCS_BUCKET env var gets injected into execution-service''s shard workers launched through this path.
  (2) `scripts/run-all-quality-gates.sh` (line 58) and `scripts/run-uv-lock-all.sh` (line 34) both list
  ''execution-services'' in their REPOS array; since the real directory is named `execution-service` and both scripts
  guard with `[ -f "$repo_path/pyproject.toml" ]` before processing an entry, the real execution-service repo is
  silently skipped by both scripts entirely. Both scripts also carry other stale entries (`ml-training-service` +
  `ml-inference-service`, consolidated into `ml-service` per a 2026-05-21 comment in shard_builder.py itself; and
  `market-tick-data-handler` instead of `market-tick-data-service`), suggesting these two scripts may be superseded
  fleet-sweep tooling rather than a one-off naming slip -- that needs to be confirmed before blindly patching them.'
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [deployment-service, naming-drift, execution-service, shard-builder, fleet-scripts, silent-gap]
related:
  [/plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md, /codex/05-infrastructure/spot-vms-for-backfill.md]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: infrastructure_master
source:
  "slot-4, backend_engineer, 2026-08-03 -- discovered while implementing
  infra_satellite_ao_dispatch_batch1_2026_07_26.md's execution-service `service_name` manifest-drift todo. Verified via
  grep+READ of shard_builder.py, worker_manager.py, _worker_rolling.py, both fleet scripts, and the real
  configs/sharding.execution-service.yaml content -- not fixed inline because both files are in deployment-service, a
  different repo than the dispatched todo's named scope (execution-service)."
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
depends_on: []
supersedes:
superseded_by:
resolved_by:
context_scope: [/plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md, deployment-service/deployment_service/shard_builder.py, deployment-service/configs/sharding.execution-service.yaml, deployment-service/scripts/run-all-quality-gates.sh]
---

# deployment-service's shard-storage-env resolver and two fleet sweep scripts key on the stale plural "execution-services" — 2026-08-03

## What I found

While fixing `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s execution-service `service_name` manifest-drift todo
(scoped to the `execution-service` repo only), I confirmed the canonical, workspace-wide identity string for this
service is the **singular** `"execution-service"` — it matches `ManifestWriter`'s 3 call sites (verified via full
`git log --all -S` on all three; the plural has never once appeared there), `ServiceBootstrap` in `cli/main.py`,
`auth.py`/`isolation_policy.py`/`config_reloaders.py`/`pre_crash_checkpoint.py`/`auth_s2s.py`, and
`deployment-api/deployment_api/services/data_status_drilldown/_core.py`'s `SERVICE_TO_KIND` registry
(`"execution-service": "execution-store"`). Most decisively, the real sharding config file on disk is named
`deployment-service/configs/sharding.execution-service.yaml` and its own `service:` field is `execution-service`
(singular).

Two gaps in **deployment-service** (a different repo than the dispatched todo's named scope) still key on the plural
form and were NOT fixed as part of that todo:

1. **`deployment_service/shard_builder.py:37`** — `_SERVICE_STORAGE_DOMAINS: dict[str, list[str]]` has the entry
   `"execution-services": ["execution-store"]`. `build_storage_env_vars(service, dimensions, config_dir)` (same file,
   ~line 223) resolves `domains = _SERVICE_STORAGE_DOMAINS.get(service, [])` — a plain `.get()` with a silent `[]`
   default, no error on miss. Its two real callers, `deployment_service/deployment/worker_manager.py:164` and
   `deployment_service/deployment/_worker_rolling.py:160`, both call it as
   `build_storage_env_vars(state.service, shard.dimensions)`, where `state.service` is populated from the sharding
   config's own `service:` field — i.e. the singular `"execution-service"` for this service. That lookup misses the dict
   entry, so `domains` resolves to `[]` and the function returns `{}` (per its own docstring: "empty dict if service has
   no mapping") — **no `EXECUTION_STORE_GCS_BUCKET` env var gets injected** into execution-service shard workers
   launched through this path. I have NOT verified whether execution-service shards are actually launched through
   `worker_manager.py`/`_worker_rolling.py` in current practice (vs. some other non-sharded launch path) — quantifying
   real-world blast radius is part of the recommended fix below, not asserted here.
2. **`deployment-service/scripts/run-all-quality-gates.sh:58`** and
   **`deployment-service/scripts/run-uv-lock-all.sh:34`** — both list `"execution-services"` in a bash `REPOS` array.
   The actual repo directory is `execution-service` (singular); both scripts guard each entry with
   `if [ -f "$repo_path/pyproject.toml" ]` before acting on it, so the real `execution-service` repo is silently skipped
   by both scripts — no error, just absent from the sweep. Both scripts ALSO list `ml-training-service` and
   `ml-inference-service` (consolidated into the single `ml-service` per a 2026-05-21 comment inside `shard_builder.py`
   itself) and `market-tick-data-handler` (the current name is `market-tick-data-service`) — three more stale entries
   beyond the one this todo is about. This pattern (multiple stale repo names, not just one) suggests these two scripts
   may be legacy/superseded fleet-sweep tooling rather than actively maintained — CLAUDE.md's own workspace-map points
   at `workspace-manifest.json` as the canonical 25-repo fleet list for this kind of sweep, which these two scripts do
   not read from.

## Why it matters

- (1) is a **silent correctness gap**, not a crash — the kind CLAUDE.md's data-pipeline/infra rules specifically call
  out as worth resolving deliberately rather than leaving live. If execution-service shard workers do go through this
  launch path, they'd be missing a bucket env var they need — a real severity question, unresolved here.
- (2) means two fleet-sweep scripts have been silently running incomplete for a while (missing execution-service, and
  carrying 3 other stale entries) — worth confirming these scripts are still load-bearing (referenced from CI, a
  runbook, or an operator habit) before spending effort patching vs. deleting them outright per the "delete deprecated
  code, no shims" HARD RULE.

## Recommended decision

- [ ] [CODE] P3. Fix `deployment_service/shard_builder.py`'s `_SERVICE_STORAGE_DOMAINS` dict key from
      `"execution-services"` to `"execution-service"` (single-line fix). Before/alongside the fix, grep+READ
      `worker_manager.py`/`_worker_rolling.py`'s callers to confirm whether execution-service shards actually flow
      through `build_storage_env_vars` in a live launch today, and add a unit test asserting
      `build_storage_env_vars("execution-service", {...})` returns a non-empty dict containing an
      `EXECUTION_STORE_GCS_BUCKET`-shaped key (mirroring how the other `_SERVICE_STORAGE_DOMAINS` entries are/should be
      tested). **Done when**: the dict key is singular, `_SERVICE_STORAGE_DOMAINS.get("execution-service")` resolves
      non-empty, a regression test pins it, and the investigation's finding (live path or not) is recorded in this
      todo's evidence. Repo: deployment-service.
- [ ] [INFRA] P3. Determine whether `scripts/run-all-quality-gates.sh` and `scripts/run-uv-lock-all.sh` (both in
      deployment-service) are still referenced by any CI workflow, runbook, or other script (grep the fleet for their
      filenames) or are dead/superseded by `workspace-manifest.json`-driven sweeps. If live: fix both REPOS arrays
      (`execution-services` → `execution-service`; drop the now-consolidated
      `ml-training-service`/`ml-inference-service` duplicates in favor of `ml-service`; `market-tick-data-handler` →
      `market-tick-data-service`) so they actually cover the current 25-repo fleet. If dead: delete both scripts per the
      "delete deprecated code, no shims" HARD RULE, after confirming zero referrers. **Done when**: either both scripts
      are corrected and re-verified against `workspace-manifest.json`'s repo list, or both are deleted with a
      referrer-check citation proving nothing points at them. Repo: deployment-service.

## Progress Log

- 2026-08-03 (slot-4, backend_engineer): Filed. Not fixed inline — both findings are in `deployment-service`, a
  different repo than `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s todo-009, which is scoped to
  `Repo: execution-service` only.
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
