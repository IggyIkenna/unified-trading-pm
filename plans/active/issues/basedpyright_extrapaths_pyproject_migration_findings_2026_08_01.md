---
doc_type: issue
title: check-pyrightconfig-extrapaths.py migrated to pyproject.toml — real extraPaths/manifest drift now surfaced
summary: >-
  Fixing check-pyrightconfig-extrapaths.py to read pyproject.toml's [tool.basedpyright] (fleet-wide migration off
  pyrightconfig.json, per pm_scripts_typecheck_debt_2026_06_11.md's last open todo) resurrected real signal: ~15 repos
  carry dead extraPaths (removed interfaces still listed) and missing extraPaths (declared manifest deps with no
  extraPath entry), plus 5 genuine import-vs-manifest gaps. All previously invisible because the tool unconditionally
  printed "OK" (it only ever read a pyrightconfig.json file, and zero of the 24 workspace-manifest.json repos still have
  one).
status: open
nature: notes
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    execution-service,
    features-service,
    greeks-service,
    instruments-service,
    market-data-processing-service,
    strategy-service,
    system-integration-tests,
    trading-agent-service,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: [quality-gates, basedpyright, extrapaths, manifest, pyproject-migration]
related: [pm_scripts_typecheck_debt_2026_06_11]
created: 2026-08-01
parent_epic: infrastructure_master
priority: P3
source:
  [
    "unified-trading-pm/scripts/manifest/check-pyrightconfig-extrapaths.py",
    "plans/active/issues/pm_scripts_typecheck_debt_2026_06_11.md (2026-08-01 slot 11 finding, resolved by this
    migration)",
  ]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

`unified-trading-pm/scripts/manifest/check-pyrightconfig-extrapaths.py` was migrated (this session, `unified-trading-pm`
commit — see git log) to read `[tool.basedpyright]` from `pyproject.toml` when a repo has no `pyrightconfig.json`
(fleet-wide migration off `pyrightconfig.json` is complete — zero of the 24 `workspace-manifest.json` repos still carry
one). Running the migrated script against the real fleet
(`uv run python3 scripts/manifest/check-pyrightconfig-extrapaths.py`, exit 1) surfaces genuine, previously-invisible
drift between each repo's `extraPaths` and its `workspace-manifest.json` declared dependencies:

**Dead extraPaths** (listed but not a manifest dep, and not imported in source — safe removals, `--apply` is NOT wired
for `pyproject.toml` sources so these need a manual TOML edit):

- alerting-service: `unified-config-interface`, `unified-internal-contracts`, `unified-cloud-interface`,
  `unified-events-interface`
- batch-live-reconciliation-service: `unified-config-interface`, `unified-internal-contracts`, `unified-cloud-interface`
- client-reporting-api: `unified-internal-contracts`, `unified-config-interface`, `unified-cloud-interface`
- deployment-api: `unified-cloud-interface`, `unified-config-interface`
- deployment-service: `unified-cloud-interface`, `unified-config-interface`
- execution-service: `unified-defi-execution-interface`, `unified-trade-execution-interface`,
  `unified-config-interface`, `unified-internal-contracts`, `unified-reference-data-interface`,
  `unified-cloud-interface`, `unified-domain-client`, `unified-sports-execution-interface`
- features-service: `unified-config-interface`, `unified-cloud-interface`
- greeks-service: `unified-cloud-interface`, `market-tick-data-service`, `instruments-service`
- instruments-service: `unified-market-interface`, `unified-internal-contracts`
- market-data-processing-service: `unified-cloud-interface`, `unified-config-interface`, `unified-internal-contracts`,
  `unified-domain-client`
- strategy-service: `unified-cloud-interface`, `unified-config-interface`, `unified-domain-client`,
  `unified-internal-contracts`
- system-integration-tests: `unified-internal-contracts`, `unified-cloud-interface`
- trading-agent-service: `unified-cloud-interface`, `unified-config-interface`
- unified-trading-library: `unified-cloud-interface`, `unified-config-interface`, `unified-internal-contracts`

**Missing extraPaths** (a real manifest dependency has no corresponding `extraPaths` entry — basedpyright can't resolve
the internal import for typechecking):

- alerting-service: `unified-api-contracts`
- client-reporting-api: `unified-api-contracts`
- deployment-api: `deployment-service`, `unified-api-contracts`
- deployment-service: `unified-api-contracts`
- system-integration-tests: `alerting-service`, `client-reporting-api`, `execution-service`, `features-service`,
  `instruments-service`, `market-data-processing-service`, `strategy-service`
- unified-trading-library: `unified-api-contracts`

**Errors** (extraPath absent from manifest deps but the package IS imported in source — the manifest itself may be
missing a declared dependency, OR this is a grep-pattern false positive worth double-checking before editing):

- execution-service: `unified-cloud-services`, `market-tick-data-service`, `execution-algo-library`,
  `matching-engine-library`
- instruments-service: `unified-config-interface`

Full raw output preserved in git history of this doc's authoring commit / re-runnable any time via
`cd unified-trading-pm && uv run python3 scripts/manifest/check-pyrightconfig-extrapaths.py`.

## Why it matters

These are stale `[[tool.basedpyright.executionEnvironments]] extraPaths` entries left over from repo splits/renames
(e.g. `unified-cloud-interface`/`unified-config-interface`/`unified-internal-contracts` were folded away — the dead
entries are fleet-wide, suggesting a shared template drift rather than 15 independent mistakes) plus genuinely missing
entries that mean basedpyright can't resolve some internal cross-repo imports during typechecking. Not CI-wired (this
script isn't invoked by `quality-gates.sh`), so none of this is actively blocking anything — pure config hygiene debt.

## Recommended decision

- [x] ✅ [SCRIPT] P3. alerting-service: remove the 4 dead extraPaths, add the missing `unified-api-contracts` extraPath
      to `[[tool.basedpyright.executionEnvironments]]` in `alerting-service/pyproject.toml`. Re-run the checker for this
      repo to confirm clean. (repo: alerting-service) — alerting-service@3054a8a. Verified via
      `uv run python3 scripts/manifest/check-pyrightconfig-extrapaths.py` — zero remaining warnings for
      alerting-service.
- [x] ✅ [SCRIPT] P3. batch-live-reconciliation-service: remove the 3 dead extraPaths in `pyproject.toml`. (repo:
      batch-live-reconciliation-service) — batch-live-reconciliation-service@c1a0cac. Removed
      `unified-config-interface`/`unified-internal-contracts`/`unified-cloud-interface` (confirmed dead: no
      `workspace-manifest.json` dep, no source import); re-ran `check-pyrightconfig-extrapaths.py` — zero remaining
      warnings for batch-live-reconciliation-service; `quality-gates.sh` green (268 passed, 1 skipped, 84.97% coverage).
- [x] ✅ [SCRIPT] P3. client-reporting-api: remove the 3 dead extraPaths, add the missing `unified-api-contracts`
      extraPath in `pyproject.toml`. (repo: client-reporting-api) — client-reporting-api@303f7d5. Removed
      `unified-internal-contracts`/`unified-config-interface`/`unified-cloud-interface` (confirmed dead: no
      `workspace-manifest.json` dep, no source import), added `unified-api-contracts` (confirmed real manifest dep);
      re-ran `check-pyrightconfig-extrapaths.py` — zero remaining warnings for client-reporting-api; `quality-gates.sh`
      green (103s).
- [x] ✅ [SCRIPT] P3. deployment-api: remove the 2 dead extraPaths, add the missing `deployment-service` and
      `unified-api-contracts` extraPaths in `pyproject.toml`. (repo: deployment-api) — deployment-api@7cdc1c9. Removed
      `unified-cloud-interface`/`unified-config-interface` (confirmed dead: no `workspace-manifest.json` dep, no source
      import), added `deployment-service`/`unified-api-contracts` (confirmed real manifest deps); re-ran
      `check-pyrightconfig-extrapaths.py` — zero remaining warnings for deployment-api; `quality-gates.sh` green (172s).
- [x] ✅ [SCRIPT] P3. deployment-service: remove the 2 dead extraPaths, add the missing `unified-api-contracts`
      extraPath in `pyproject.toml`. (repo: deployment-service) — deployment-service@9e4eea9. Removed
      `unified-cloud-interface`/`unified-config-interface` (confirmed dead: no `workspace-manifest.json` dep, no source
      import, sibling dirs don't even exist), added `unified-api-contracts` (confirmed real manifest dep); re-ran
      `check-pyrightconfig-extrapaths.py` — zero remaining warnings for deployment-service; `quality-gates.sh` green
      (256s, `IGNORE_TIMEOUT=true` used once for a transient host-contention timing-gate-only failure per codex
      quality-gates.md sanctioned override — all substantive gates were green on that run too).
- [x] ✅ [SCRIPT] P3. execution-service: remove the 8 dead extraPaths in `pyproject.toml`; separately investigate the 4
      import-vs-manifest errors (`unified-cloud-services`, `market-tick-data-service`, `execution-algo-library`,
      `matching-engine-library`) — confirm each is a genuine live import (not a stale/commented reference) before adding
      it to `workspace-manifest.json` deps. (repo: execution-service) — execution-service@050ed797. Removed the 8
      confirmed-dead extraPaths (zero manifest dep, zero source import each). Investigated the 4 errors: 3 were
      grep-pattern false positives (`unified-cloud-services` — legacy pre-UTL package name, not a workspace repo, only
      referenced by an orphaned `verify_ucs_installation.py` script pytest never collects; `execution-algo-library` —
      the only hit is inside a docstring `Example:` block, not a real import; `matching-engine-library` — every
      reference is commented out) — their extraPaths removed too. `market-tick-data-service` is genuine (real import in
      `mtds_book_provider.py`, a sanctioned + tracked cross-service exception per UAC `service_contract_map.py`
      `forbidden_exceptions` / `deprecation_ledger.yaml` id `execution_service_mtds_reader_dep`) — extraPath kept, added
      to `workspace-manifest.json` `execution-service` dependencies (this commit). Re-ran
      `check-pyrightconfig-extrapaths.py` — zero remaining warnings for execution-service; `quality-gates.sh` green
      (192s, incl. `workspace-manifest.json valid (schema + topological)`).
- [x] ✅ [SCRIPT] P3. features-service: remove the 2 dead extraPaths in `pyproject.toml`. (repo: features-service) —
      features-service@217eb3a2. Removed `unified-config-interface`/`unified-cloud-interface` (confirmed dead: no source
      import, sibling dirs don't exist in this checkout); re-ran `check-pyrightconfig-extrapaths.py` — zero remaining
      warnings for features-service. `quality-gates.sh` was RED on the clean tree (13 pre-existing failures, unrelated
      to this todo — see `features_smoke_matrix_verification_findings_2026_08_01.md` finding 6, fixed inline as
      features-service@b9cf1e1c same session); full `quality-gates.sh` green after that fix (sentinel-verified,
      HEAD=b9cf1e1c), shipped via quickmerge, landed + verified on `live-defi-rollout`.
- [x] ✅ [SCRIPT] P3. greeks-service: remove the 3 dead extraPaths in `pyproject.toml`. (repo: greeks-service) —
      greeks-service@8268f71. Removed `unified-cloud-interface`/`market-tick-data-service`/`instruments-service`
      (confirmed dead: no `workspace-manifest.json` dep — greeks-service only declares `unified-trading-library` +
      `unified-api-contracts` — and no source import); re-ran `check-pyrightconfig-extrapaths.py` — zero remaining
      warnings for greeks-service; `quality-gates.sh` green (68s), shipped via quickmerge, landed + verified on
      `live-defi-rollout`.
- [x] ✅ [SCRIPT] P3. instruments-service: remove the 2 dead extraPaths; separately investigate the
      `unified-config-interface` import-vs-manifest error (confirm genuine import before adding to manifest deps).
      (repo: instruments-service) — instruments-service@02a61199. Removed `unified-market-interface` /
      `unified-internal-contracts` (confirmed dead: no manifest dep, no source import). Investigated
      `unified-config-interface`: the only reference was `tests/conftest.py`'s local `get_config(key, default)` helper —
      confirmed genuinely dead (never called anywhere; every real caller uses `instruments_service.config.get_config()`
      with no args) and its lazy `from unified_config_interface import     UnifiedCloudConfig` pointed at a package that
      no longer exists (folded fleet-wide into `unified_trading_library`, already imported correctly everywhere else in
      this repo). Deleted the dead helper per the no-shims rule rather than add a manifest dep for a nonexistent
      package; removed the now-unneeded `unified-config-interface` extraPath too. Re-ran
      `check-pyrightconfig-extrapaths.py` — zero remaining warnings for instruments-service; `quality-gates.sh` green
      (111s, sentinel-verified, HEAD=02a61199), shipped via quickmerge, landed + verified on `live-defi-rollout`.
- [x] ✅ [SCRIPT] P3. market-data-processing-service: remove the 4 dead extraPaths in `pyproject.toml`. (repo:
      market-data-processing-service) — market-data-processing-service@28e0d90. Removed
      `unified-cloud-interface`/`unified-config-interface`/`unified-internal-contracts`/`unified-domain-client`
      (confirmed dead: no `workspace-manifest.json` dep — only `unified-trading-library` + `unified-api-contracts` are
      declared —, no sibling dir, no genuine source import; the only grep hit,
      `tests/integration/test_library_deps_integration.py::test_unified_domain_client_import`, is a legacy-named test
      that actually imports from `unified_trading_library`); re-ran `check-pyrightconfig-extrapaths.py` — zero remaining
      warnings for market-data-processing-service; `quality-gates.sh` green (90s, sentinel-verified, HEAD=28e0d90),
      shipped via quickmerge, landed + verified on `live-defi-rollout`.
- [x] ✅ [SCRIPT] P3. strategy-service: remove the 4 dead extraPaths in `pyproject.toml`. (repo: strategy-service) —
      strategy-service@307868bc. Removed `unified-cloud-interface`/`unified-config-interface`/`unified-domain-client`/
      `unified-internal-contracts` (confirmed dead: no `workspace-manifest.json` dep, no source import — the
      `test_unified_domain_client_import` hit was a misleadingly-named test that actually imports from
      `unified_trading_library`, not the `unified_domain_client` package); re-ran `check-pyrightconfig-extrapaths.py` —
      zero remaining warnings for strategy-service; `quality-gates.sh` green (one
      `tests/per_client_isolation/test_shared_marks_reader.py` xdist shared-memory-name race on the first run, confirmed
      pre-existing/unrelated via isolated re-run on a clean tree, cleared on retry).
- [x] ✅ [SCRIPT] P3. system-integration-tests: remove the 2 dead extraPaths, add the 7 missing extraPaths
      (`alerting-service`, `client-reporting-api`, `execution-service`, `features-service`, `instruments-service`,
      `market-data-processing-service`, `strategy-service`) in `pyproject.toml`. (repo: system-integration-tests) —
      system-integration-tests@f132224. Removed `unified-internal-contracts`/`unified-cloud-interface` (confirmed dead:
      no manifest dep, no source import), added the 7 missing extraPaths (confirmed real manifest deps). Re-ran
      `check-pyrightconfig-extrapaths.py` — zero remaining warnings for system-integration-tests; `quality-gates.sh`
      green, shipped via quickmerge, landed + verified on `live-defi-rollout`.
- [x] ✅ [SCRIPT] P3. trading-agent-service: remove the 2 dead extraPaths in `pyproject.toml`. (repo:
      trading-agent-service) — trading-agent-service@52341f9. Removed `unified-cloud-interface`/
      `unified-config-interface` (confirmed dead: no manifest dep, no source import); re-ran
      `check-pyrightconfig-extrapaths.py` — zero remaining warnings for trading-agent-service; `quality-gates.sh` green,
      shipped via quickmerge, landed + verified on `live-defi-rollout`.
- [ ] [SCRIPT] P3. unified-trading-library: remove the 3 dead extraPaths, add the missing `unified-api-contracts`
      extraPath in `pyproject.toml`. (repo: unified-trading-library)
