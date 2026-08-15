---
doc_type: issue
title:
  execution-service Verification-Debt Findings — DeFi Address Duplication, Untested Exception Widen, Dormant slot_label
  Proxy
summary:
  Three findings from a read-only production-verification audit of already-shipped execution-service commits (cc3e07e0c,
  2b92d6ac6) and the removed v2/handlers.py — a residual local duplicate of UAC's DeFi LST address SSOT, an untested
  exception-handling widen in the GCS data loaders, and a dormant (deleted, not fixed-in-place) unverified
  strategy_instance_id-as-slot_label substitution. No fixes applied during the audit; scoped here for AO dispatch.
status: open
nature: process
resolved_by:
asset_group: [defi]
stage: [execution]
repos: [execution-service, unified-api-contracts]
scope: [engineer]
tags: [audit, verification-debt, defi, code-quality]
related:
  [
    /plans/active/issues/strategy_service_verification_debt_findings_2026_08_15.md,
    /plans/active/issues/pm_archive_false_done_and_review_backlog_2026_08_15.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: execution_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1
effort: medium
locked_by:
locked_since:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/lst_token_addresses.py,
    execution-service/execution_service/defi_execution/protocols/lido.py,
    execution-service/execution_service/defi_execution/protocols/rocket_pool.py,
    execution-service/execution_service/defi_execution/protocols/etherfi.py,
    execution-service/execution_service/defi_execution/protocols/renzo.py,
    execution-service/execution_service/defi_execution/protocols/puffer.py,
    execution-service/execution_service/v2/policy_resolver.py,
    execution-service/execution_service/engine/routing/handler_registry.py,
    unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py,
    execution-service/execution_service/data/loader_transforms.py,
    execution-service/execution_service/data/loaders/base.py,
  ]
supersedes:
superseded_by:
depends_on:
source: production_verification_debt_audit_2026_08_15
assigned_role: backend_engineer
drift_direction: advance-code
---

# execution-service Verification-Debt Findings (2026-08-15 Audit)

> Read-only verification audit of production commits already shipped in execution-service. No fixes were applied —
> findings are scoped below for AO dispatch to decide execution order. Small plan (3 todos); the archival step is folded
> into the final todo rather than spun into a separate companion finalize plan, per `task_template.md` §4's single-todo-
> scale exception (this plan is a few todos, not one, but the archival overhead of a separate file is disproportionate
> to its size).

## Findings → todos

- [ ] [BACKEND] P2. Replace execution-service's hardcoded LST address constants (`STETH_ADDRESS`, `WSTETH_ADDRESS`,
      `RETH_ADDRESS`, `WEETH_ADDRESS`, `EZETH_ADDRESS`, `PUFETH_ADDRESS` in
      `execution_service/defi_execution/protocols/{lido,rocket_pool,etherfi,renzo,puffer}.py`) with imports from
      `unified_api_contracts.registry.lst_token_addresses` — the same import strategy-service's
      `position_interface/capabilities.py`/`factory.py` already use. Today execution-service carries a residual local
      duplicate of the exact addresses UAC's `lst_token_addresses.py` was built to be the single source of truth for
      (its own docstring states duplicating them "would have created a second source of truth"); values currently agree
      only because UAC was derived from these, but a future edit to either side won't propagate. Repo:
      execution-service. Done-when: grep for the 6 hardcoded hex-literal constants in `defi_execution/protocols/`
      returns zero hits, both repos' `quality-gates.sh` are green.

- [ ] [BACKEND] P3. Add unit-test coverage for the `GoogleAPICallError` catch that 2b92d6ac6 added to the GCS
      blob-existence probe in `loader_transforms.py` and `loaders/base.py` (widened from
      `(OSError, ConnectionError, TimeoutError, ValueError)`) — currently zero tests reference this exception type, so a
      regression re-narrowing the catch tuple would go undetected. Repo: execution-service. Done-when:
      `tests/unit/data/test_loader_transforms.py` and `test_loaders_base.py` each have a passing case that raises
      `google.api_core.exceptions.GoogleAPICallError` from the probe and asserts the loader falls back to the
      canonical-first candidate path instead of propagating.

- [ ] [BACKEND] P3. Add a fail-loud guard (explicit `None`/shape check, not a silent pass-through) to
      `ExecutionPolicyResolver.resolve()` / `resolve_config_algorithm()` in `execution_service/v2/policy_resolver.py`,
      plus a one-line docstring note citing this finding, so that when `HandlerRegistry.select_algorithm`'s `slot_label`
      wiring is eventually reactivated (currently zero live callers anywhere in execution-service — confirmed via a
      repo-wide grep), a future integrator cannot silently repeat the deleted `v2/handlers.py` precedent of substituting
      `identity.strategy_instance_id` for `slot_label`. Per UAC's `TradingWalletConfig` docstring
      (`unified_api_contracts/internal/domain/defi/wallet_config.py`), a bare `strategy_id`/`strategy_instance_id`
      "cannot distinguish two instances of one archetype on different venues, which is the normal case" — only
      `slot_label` is the real v2 instance identity. Repo: execution-service. Done-when: `policy_resolver.py` raises or
      logs fail-loud on an unset/placeholder `slot_label` rather than accepting any string silently, and this todo's
      checkbox is flipped with a commit citing the change; once all three todos above are `[x]`, run the standard
      archival ritual on this doc (git mv to `plans/archive/2026_08/`, corpus-wide referrer fixup) in the same commit
      that flips this checkbox.

## Progress Log

- **2026-08-15**: Filed from a read-only production-verification-debt audit (8-item priority list, this doc covers the 3
  execution-service items: DeFi address provenance/duplication, 2b92d6ac6 scope-creep review, and the slot_label proxy
  claim). Companion docs for the strategy-service and unified-trading-pm findings from the same audit:
  `strategy_service_verification_debt_findings_2026_08_15.md`, `pm_archive_false_done_and_review_backlog_2026_08_15.md`.
