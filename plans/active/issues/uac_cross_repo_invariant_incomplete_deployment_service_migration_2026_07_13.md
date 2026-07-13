---
doc_type: issue
title: unified-api-contracts cross-repo invariant test RED — deployment-service registry relocation incomplete
summary:
  test_deployment_service_cross_repo_invariant.py::test_deployment_service_registry_surface_stable fails because
  deployment-service@b665123e deleted deployments_registry.py (intending to relocate it to unified-trading-library) but
  the module does not exist yet in unified-trading-library — the migration is only half-landed.
status: open
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
author: slot-11
source: [utl_reuse_phase7_low_lint_tail_2026_07_13.md, slot-11 backend-engineer task]
resolved_by:
locked_by:
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

- [ ] [CODE] P1. Land `deployments_registry.py` (or its renamed equivalent) in `unified-trading-library`, matching what
      `deployment-service@b665123e` already assumes exists there — OR revert that deletion until the UTL side is ready.
      (repo: unified-trading-library or deployment-service)
- [ ] [CODE] P2. Update
      `unified-api-contracts/tests/test_deployment_service_cross_repo_invariant.py::     test_deployment_service_registry_surface_stable`
      to check the NEW location once landed (mirror the `_module_level_import_names` re-export-recognition pattern
      already added for the VM_PREFIX_TO_BUCKET sibling test in `unified-api-contracts@4bbc7276` if the new home also
      re-exports rather than directly assigning). (repo: unified-api-contracts)
- [ ] [VERIFY] P1. Once landed, re-run `bash scripts/quality-gates.sh` in unified-api-contracts full-green, then resolve
      the repo-blocker / flip the `repo-unified-api-contracts-qg-green` condition. (repo: unified-api-contracts)
