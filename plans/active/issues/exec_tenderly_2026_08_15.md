---
doc_type: issue
title: execution-service RecursiveLoopOrchestrator Tenderly-fork integration test is credential-blocked
summary: >-
  `execution-service/tests/defi_execution/unit/test_recursive_loop_orchestrator.py::test_tenderly_fork_full_cycle`
  exercises a 5-loop wstETH/WETH E-Mode open+unwind against a live Aave V3 pool via a Tenderly fork RPC. No Tenderly
  fork endpoint/API key is provisioned in this workspace's ambient credential set (GSM/CI secrets), so the test is
  `@pytest.mark.skip`ped pending provisioning. Filed to satisfy `check_xfail_skip_tracked.py`'s tracked-slug requirement
  (`ci-reconcile` root-caused this as the sole `quality-gates-v2` red on `execution-service` live-defi-rollout push
  `37bfaeed`, a genuine new-code push wiring real Uniswap/Lido/Jupiter/Aave/Kamino/Jito dispatch — the skip marker
  landed with that commit but without a tracking citation).
status: open
nature: issue
asset_group: [defi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [credential-blocked, tenderly, aave-v3, integration-test, defi-execution]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md,
  ]
created: 2026-08-15
author: ci_reconciler (agt-f0dda8, slot 8)
source: ci_reconciler CI sweep (quality-gates-v2 red on execution-service live-defi-rollout push 37bfaeed)
parent_epic: defi_master
priority: P3
assigned_vm: NA
execution_scope: local-only
locked_by:
locked_since:
context_scope: [execution-service/tests/defi_execution/unit/test_recursive_loop_orchestrator.py, /codex/02-data/external-data-always-available-rule.md]
supersedes:
superseded_by:
depends_on: []
resolved_by:
drift_direction: advance-code
---

# execution-service Tenderly-fork Aave V3 integration test — credential-blocked

## What was found

`test_tenderly_fork_full_cycle` (RecursiveLoopOrchestrator 5-loop wstETH/WETH E-Mode open+unwind, Phase-4-deployed
receiver) requires a live Tenderly fork RPC endpoint plus real Aave V3 pool access. Neither is provisioned in this
workspace's ambient GSM/CI credential set. The test is correctly `@pytest.mark.skip`-ped rather than fabricating a pass,
per `/codex/02-data/external-data-always-available-rule.md`'s BLOCKED-CREDENTIALS pattern — the adapter/test scaffold
already exists and is wired, it just cannot execute against live infra without the credential.

## Todos

- [ ] [OPERATOR] P3. Provision a Tenderly fork RPC endpoint + API key (and confirm Aave V3 pool read/write access
      through it) for `execution-service` CI, then un-skip `test_tenderly_fork_full_cycle` and verify it passes against
      the live fork.
- **na-eligibility-audit 2026-08-16** [body-hash:4939ad84f015af58]: KEEP-NA, valid — Single open todo requires provisioning a live Tenderly fork RPC endpoint + API key (with confirmed Aave V3 pool read/write access) to un-skip `test_tenderly_fork_full_cycle` — no such credential exists in the workspace's ambient GSM/CI secret set, and this cannot be self-served by an agent.

## Progress Log

**context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
**na-eligibility-audit 2026-08-17** (defi tranche, dispatch agt-f4fef7): KEEP-NA, valid — re-confirmed; no
substantive content change since the 2026-08-16 verdict (context-scout metadata touch only). Sole open todo still
requires operator-provisioned Tenderly fork RPC + API key, not agent-self-serviceable. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, valid — re-confirmed; sole open todo still requires an operator-provisioned Tenderly fork RPC + API key, not agent-self-serviceable. Doc stays `assigned_vm: NA`.
