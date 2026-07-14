---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 9 deployment-api→deployment-service registry extraction
summary:
  Relocate the shared deployments_registry GCS accessor from deployment-service into UTL so both deployment-api and
  deployment-service import it from UTL, removing the last service-dep edge; plus a deferred hardening item.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, service-deps, split]
related: [plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
locked_by: live-defi-rollout
locked_since: "2026-07-13"
supersedes:
superseded_by:
depends_on:
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend_engineer
drift_direction: advance-code
---

# UTL/UAC reuse consolidation — Phase 9 service-dep violations (remainder)

> **Split provenance (2026-07-13):** Phase 9 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md)
> (operator sweep 2026-06-10) — the dead-gate fix, gate enable, and 3 of 4 violations already shipped, reproduced below
> as done. Independent of every other split plan — no gate. **This plan's item does NOT block Phase 7/8's gate**,
> matching the tracker's own note that `deployment-service` is manifest `type=infrastructure`, so
> `check-no-service-deps.py` doesn't flag this edge even though it's still open.

## Todos

- [x] ✅ [AGENT] P1. **DEAD-GATE FIX — DONE (path + types + parser + enable):** `unified-trading-pm@1496b40f` (PR #242)
      — corrected `base-service.sh` to invoke `scripts/validation/check-no-service-deps.py` (the prior
      `scripts/check-no-service-deps.py` path never existed → gate silently no-op'd fleet-wide) + surfaced stderr;
      broadened `get_service_repos()` to `type ∈ {service, api-service, batch-service, api}` (keeps
      library/infrastructure/tool/devops/ui/test-harness non-service); fixed `get_path_deps()` to parse BOTH the FLAT
      `[tool.uv.sources]` and the DOTTED `[tool.uv.sources.<dep>]` table forms (the path-only flat parse missed mdps's
      dotted mtds dep); +4 regression unit tests (`tests/unit/test_check_no_service_deps.py`, 16 pass). Enabled LAST,
      after the mdps + deployment-api violations were remediated. **REMAINING (deferred, P2 — see last item below):**
      extend the check to also catch a raw `import <other_service>` in source/tests (currently path-dep-only) — the
      path-dep gate already catches every live violation; the import-level extension is additive hardening.
- [x] ✅ [AGENT] P1. **TRUE VIOLATION — deployment-api → strategy-service — DONE.** Relocated `compute_unified_nav` +
      `compute_nav_by_client` (+ the `_make_stub_balance` helper) from `strategy_service.position.core.treasury_monitor`
      into UTL `unified_trading_library/treasury/nav_rollup.py` (`unified-trading-library@6e3eb3c5`; +
      `test_nav_rollup.py` moved with the code, 13 tests; exported from BOTH `treasury/__init__` and the UTL top-level
      facade so consumers use `from unified_trading_library import compute_unified_nav`). strategy-service deleted the
      functions, keeps the `TreasuryMonitor` class local (`strategy-service@573f09d8`). deployment-api
      `treasury_routes.py` now imports from the UTL facade + DROPPED the `[tool.uv.sources]` strategy-service path-dep +
      dep line + marked the 3 FastAPI DTOs `# CORRECT-LOCAL` (`deployment-api@0a9600a9`). Removes the service→service
      edge. Dep order: UTL→strategy-service→deployment-api; all QG exit 0.
- [x] ✅ [AGENT] P1. **deployment-api → deployment-service — EXTRACT the shared registry to UTL — DONE.** Relocated
      `deployments_registry.py` (529 lines: `DeploymentsRegistry` + `DeploymentRegistryEntry` + VM-log URI helpers +
      `is_entry_stale`) into UTL as `unified_trading_library.deployment_registry` (`unified-trading-library@5926c6f0`;
      +32 tests moved with the code, re-exported from the top-level facade under plain names per the workspace's
      top-level-import-only convention — fixed 2 latent basedpyright `reportArgumentType` errors + a QG
      empty-dict-fallback + method-size violation surfaced by UTL's stricter gates). deployment-service repointed all 8
      in-repo consumers (heartbeat*cli, deployment_heartbeat, vm_zombie_watchdog, vm_serial_capture_cron,
      vm_log_archival_cron, 3 tests) to the UTL import and deleted its local copy (`deployment-service@b665123e`).
      deployment-api repointed all 8 routes + removed the now-dead `deployment_service.deployments_registry` test-stub
      scaffolding (`deployment-api@a7978bc3`). Removes the service→service edge with no forced HTTP boundary;
      deployment-service keeps `type=service`. Dep order: UTL→deployment-service→deployment-api; all 3 QG exit 0
      (deployment-api's basedpyright error count actually \_dropped* 591→201 since the registry now resolves through a
      cleanly-typed UTL module instead of an unresolved cross-service import).
- [x] ✅ [AGENT] P2. **market-data-processing-service → market-tick-data-service — DONE.** Relocated
      `databento_classifier` (825 lines, UAC-only deps) to UAC `unified_api_contracts/external/databento/` + its test
      suite (`unified-api-contracts@00a7aca9`; +15 tests for the previously-uncovered paths to hold UAC's 94% coverage
      floor). mtds repointed `databento_adapter`/`databento_equity`/`__init__` + 2 tests to UAC and DELETED its local
      copy + dedicated test (`market-tick-data-service@9a34a43c`). mdps `canonical_writer.py` now imports
      `from unified_api_contracts.external.databento import classify_databento_symbol` + DROPPED the
      `[tool.uv.sources.market-tick-data-service]` path-dep + dep line (`market-data-processing-service@294b59ff`).
      Removes the cross-service deep-import. `external.{source}` is the sanctioned UAC external surface (not a banned
      `canonical.*` deep import). Dep order: UAC→mtds→mdps; all QG exit 0.
- [x] ✅ [AGENT] P2. **strategy-service → market-tick-data-service** — DONE: `strategy-service@d1f5a6a8` (test +
      pyproject + uv.lock) + `unified-trading-pm@4af80fd83` (manifest edge). The sole coupling was
      `test_split_libraries.py::test_market_interface_import`, which only asserted MTDS's `get_market_adapter` is
      importable — i.e. it tested MTDS, not strategy (verified 0 MTDS imports in strategy source). Deleted that test +
      removed the `[project.dependencies]` entry + `[tool.uv.sources]` block + re-locked (dropped MTDS and its
      transitive-only `websocket-client`/`yfinance`) + removed the manifest dependency edge (alignment: True). Removes
      the service→service violation AND the test-only path-dep that gated every strategy ship (the 2026-06-10 dirty-MTDS
      ship-block root cause). QG exit 0 both repos.
- [x] ✅ [VERIFY] P1. **Gate ENABLED + fleet-verified — DONE** (`unified-trading-pm@1496b40f`). The two gate-CAUGHT
      path-dep edges (mdps→mtds, deployment-api→strategy-service) are resolved, so `check-no-service-deps.py` now exits
      0 across ALL 15 service-flavoured repos (verified by running the fixed gate from each repo dir with `REPO_ROOT`
      set). +4 regression unit tests added. **NOTE — edge #4 (deployment-api → deployment-service, P1 item above) is
      still OPEN but does NOT block enablement**: `deployment-service` is manifest `type=infrastructure`, NOT a
      service-flavour, so the gate correctly does not flag that path-dep (it is a library-like-coupling extraction, not
      a service↔service violation in the gate's terms). The stale manifest dep-edges for the 2 resolved edges were
      dropped via `fix-internal-dependency-alignment.py` (alignment: True).
- [x] ✅ [AGENT] P2. **DEFERRED (additive hardening) — extend `check-no-service-deps.py` to also catch a raw
      `import <other_service>` in source/tests** (currently `[tool.uv.sources]` path-dep-only). Today every LIVE
      service↔service violation also carries a path dep, so the path-dep gate catches them all; this extension is
      belt-and-suspenders for a future import-without-path-dep case. Target repo: `unified-trading-pm`
      (`scripts/validation/check-no-service-deps.py`). — SHIPPED `unified-trading-pm@386a7325` (companion fleet-drift
      fix `unified-trading-pm@5e056fad` — see below). Added `find_raw_service_imports()`: AST-walks every `.py` file
      under the current service repo (source + tests, skipping `.venv`/build dirs) for a plain `import <pkg>` or
      `from <pkg>[.sub] import ...` whose top-level component matches another service's importable package name
      (dash→underscore of its manifest repo key). **Deliberately WARN-only (prints `[WARN]`, does not fail the gate)** —
      a fleet-wide sanity probe (all 24 repos, before shipping) found ~11 hits across
      execution-service/features-service/strategy-service, every one an already-reviewed/tracked cross-service import
      (`service_contract_map.py forbidden_exceptions`, `deprecation_ledger.yaml`, or an explicit sanctioned-deep-import
      rationale comment). Hard-failing on those today would break 3 repos' `quality-gates.sh` outside this plan's
      declared scope with no way to distinguish new accidental coupling from sanctioned debt — mirrors how the original
      path-dep gate itself was rolled out (detector → remediate/baseline → hard-fail last, item 1 above); that
      remediation pass is out of this ticket's scope and is a tracked follow-up, not silently dropped. Verified via 29
      new/updated unit tests (`tests/unit/test_check_no_service_deps.py`, including 3 end-to-end `main()` tests proving
      raw-import hits warn+exit-0 while a path-dep still hard-fails+exit-1) — 941 passed / 8 skipped full-suite;
      `ruff`/`basedpyright` clean; re-ran the fleet-wide probe post-format, all 24 repos still exit 0. **Unrelated
      blocker hit + fixed in passing**: PM's Stage 1.5 dependency-alignment gate was red on an unrelated fleet-canonical
      `click` floor (`>=8.3.2` vs the already-tightened PYSEC-2026-2132 fix `>=8.3.3`, per
      `plans/active/issues/fund_administration_service_click_pysec_2026_2132_2026_07_13.md` — documented as already
      corrected in that same session but never pushed) — completed + shipped that one-line fix
      (`unified-trading-pm@5e056fad`, `workspace-constraints.toml` + regenerated `canonical-dependency-manifest.json`)
      since it blocked every PM quickmerge, not just this one.

## Success criteria

`deployments_registry` relocated to UTL, both deployment-api and deployment-service import it from there; the
import-level gate hardening item is tracked (not blocking).

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
