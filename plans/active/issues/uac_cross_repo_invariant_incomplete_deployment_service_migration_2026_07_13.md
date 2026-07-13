---
doc_type: issue
title: unified-api-contracts cross-repo invariant test RED — deployment-service registry relocation incomplete
summary:
  test_deployment_service_cross_repo_invariant.py::test_deployment_service_registry_surface_stable fails because
  deployment-service@b665123e deleted deployments_registry.py (intending to relocate it to unified-trading-library) but
  the module does not exist yet in unified-trading-library — the migration is only half-landed.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, deployment-service, unified-trading-library]
scope: [engineer]
tags: [cross-repo-test, migration, repo-blocker]
related: [plans/active/issues/execution_service_codex_compliance_red_2026_07_13.md]
created: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source: [utl_reuse_phase7_low_lint_tail_2026_07_13.md, slot-11 backend-engineer task]
resolved_by: slot-3
locked_by:
drift_direction: advance-code
depends_on: []
---

# unified-api-contracts cross-repo invariant test RED — deployment-service registry relocation incomplete

## What I found

While shipping an unrelated UAC change (`unified_api_contracts/registry/service_contract_map.py`, sanctioning the
execution-service→MTDS reader import, part of `utl_reuse_phase7_low_lint_tail_2026_07_13.md`),
`bash scripts/quality-gates.sh` failed on
`tests/test_deployment_service_cross_repo_invariant.py:: test_deployment_service_registry_surface_stable`:

```
AssertionError: deployment_service/deployments_registry.py missing at
  .../deployment-service/deployment_service/deployments_registry.py
```

`deployment-service@b665123e` ("feat(deployment-registry): relocate deployments_registry.py to unified-trading-library")
deleted the file from deployment-service. But `unified-trading-library` has no `deployments_registry.py` (or equivalent
module) anywhere in its tree as of this writing — the migration's other half hasn't landed. This is NOT caused by my
diff.

A sibling failure in the SAME test file surfaced earlier in the same session
(`test_deployment_service_vm_zombie_watchdog_stable` — `VM_PREFIX_TO_BUCKET` re-exported via
`from deployment_service.vm_prefix_registry import VM_PREFIX_TO_BUCKET` instead of a direct module-level assignment) was
fixed upstream mid-session by another slot (`unified-api-contracts@4bbc7276`) while I was working — I rebased it in.
This second failure (the full-file relocation) has not been fixed yet; verified twice via two separate full
`quality-gates.sh` runs (12:12 UTC and 12:52 UTC), same failure both times, ~40 minutes apart.

## Why it matters

This cross-repo invariant test suite runs unconditionally in UAC's `quality-gates.sh` — it blocks ALL shipping to UAC
(not just mine) while deployment-service is mid-migration on a repo it monitors. A partially-landed cross-repo move
(delete-then-relocate as two separate commits, instead of one atomic PR spanning both repos, or a
`status: draft`/deprecation-ledger tracked intermediate state) leaves every OTHER shipper blocked in the gap.

## Recommended decision

Whoever owns the `deployments_registry.py` relocation: land the `unified-trading-library` side (or revert the
deployment-service deletion until the destination is ready) so the module exists at ITS new home, then update
`test_deployment_service_registry_surface_stable`'s expected location to match. Until then, this specific test should
either skip cleanly (recognizing the migration is in-flight) or the relocation should be tracked in
`deprecation-ledger.yaml` with a `status: parallel` entry so this exact whiplash doesn't repeat for the next mid-flight
cross-repo move.

## Todos

- [x] ✅ [CODE] P1. Land `deployments_registry.py` (or its renamed equivalent) in `unified-trading-library`, matching
      what `deployment-service@b665123e` already assumes exists there — OR revert that deletion until the UTL side is
      ready. (repo: unified-trading-library or deployment-service) — Already landed by another slot before I picked this
      up: `unified-trading-library@5926c6f0` ("feat(deployment-registry): relocate deployments_registry.py from
      deployment-service"), as `unified_trading_library/deployment_registry.py` (589 lines, all 12 symbols exported
      including `DEFAULT_BUCKET`/`DeploymentRegistryEntry`/`DeploymentsRegistry`/`coerce_host_metrics_window`/
      `vm_serial_rolling_uri`/`InMemoryStorageClient`), with its own 544-line test suite. Verified deployment-api's
      consumers (`deployments_inventory.py`, `monitor_scheduled.py`, `monitor_backfill.py`, `vm_deployments.py`,
      `monitor_experiments.py`, `vm_admin.py`, `_vm_health.py`, `monitor_live.py`) already import from
      `unified_trading_library` directly — the migration's consumer side was already fully complete too.
- [x] ✅ [CODE] P2. Update
      `unified-api-contracts/tests/test_deployment_service_cross_repo_invariant.py::test_deployment_service_registry_surface_stable`
      to check the NEW location once landed (mirror the `_module_level_import_names` re-export-recognition pattern
      already added for the VM_PREFIX_TO_BUCKET sibling test in `unified-api-contracts@4bbc7276` if the new home also
      re-exports rather than directly assigning). (repo: unified-api-contracts) — SHIPPED
      `unified-api-contracts@de13f4bc`: added a `_utl_root()` helper + a UTL-sibling skip guard (mirroring the existing
      `_skip_if_absent()` pattern), repointed the test at
      `unified-trading-library/unified_trading_library/deployment_registry.py`, updated the file's module docstring.
      UTL's file defines the 5 expected names directly (no re-export layer needed — the
      `_module_level_assign_names`/`_function_names`/`_class_names` union already used for this test covers it).
- [x] ✅ [VERIFY] P1. Once landed, re-run `bash scripts/quality-gates.sh` in unified-api-contracts full-green, then
      resolve the repo-blocker / flip the `repo-unified-api-contracts-qg-green` condition. (repo: unified-api-contracts)
      — All 6 tests in `test_deployment_service_cross_repo_invariant.py` pass. Full `quality-gates.sh` exit 0, sentinel
      verified matching HEAD (`de13f4bc`). Shipped via quickmerge, landed on `live-defi-rollout`. No open repo-blocker
      was found registered for this condition at resolution time.
