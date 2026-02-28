---
name: Rename 6 Repos Consistency
overview: "Rename 6 repos for naming consistency: market-tick-data-handler to market-tick-data-service, execution-service to execution-service, alerting-service to alerting-service, client-reporting-api to client-reporting-api, infra to ibkr-gateway-infra, api-contracts to unified-api-contracts. Update all pyproject.toml, imports, manifest, docs, configs, SVGs, and re-install venvs."
todos:
  - id: rename-infra
    content: Rename infra -> ibkr-gateway-infra (directory, GitHub, manifest, docs)
    status: completed
  - id: rename-alerting
    content: Rename alerting-service -> alerting-service (directory, GitHub, package, imports, manifest, configs, docs)
    status: completed
  - id: rename-client-reporting
    content: Rename client-reporting-api -> client-reporting-api (directory, GitHub, package, imports, manifest, configs, docs)
    status: completed
  - id: rename-mtdh
    content: Rename market-tick-data-handler -> market-tick-data-service (directory, GitHub, package, imports, fix exec dep, manifest, configs, docs)
    status: completed
  - id: rename-execution
    content: Rename execution-service -> execution-service (directory, GitHub, package, imports, manifest, configs, docs, cursor rules)
    status: completed
  - id: rename-api-contracts
    content: Rename api-contracts -> unified-api-contracts (directory, GitHub, package, 17+ pyproject.toml, 8+ import repos, cursor rules, codex docs)
    status: completed
  - id: rebuild-svgs-post-rename
    content: Rebuild both SVGs + verify xmllint, re-install venvs in all affected repos, update consolidated plan
    status: completed
isProject: false
---

# Rename 6 Repos for Naming Consistency

## Execution Order (smallest blast radius first)

### Phase 1: Zero-dependency renames (no cross-repo Python imports)

**1. infra -> ibkr-gateway-infra**

- Rename directory: `mv infra ibkr-gateway-infra`
- GitHub: `cd ibkr-gateway-infra && gh repo rename ibkr-gateway-infra`
- Update: workspace-manifest.json (repo entry + topologicalOrder L0)
- Update: SVGs, plan files (~5 references)
- No pyproject.toml changes needed (repo has no pyproject.toml)

**2. alerting-service -> alerting-service**

- Rename directory: `mv alerting-service alerting-service`
- GitHub: `cd alerting-service && gh repo rename alerting-service`
- Rename Python package: `mv alerting_service/ alerting_service/` inside repo
- Update self pyproject.toml: `name = "alerting-service"`
- Update all internal imports: `from alerting_service` -> `from alerting_service`
- Update: workspace-manifest.json, runtime-topology.yaml, sharding configs, codex docs, SVGs (~10 refs)
- Re-install: `cd alerting-service && uv pip install -e ".[dev]"`

**3. client-reporting-api -> client-reporting-api**

- Rename directory + GitHub
- Rename Python package: `client_reporting_api/` -> `client_reporting_api/`
- Update self pyproject.toml
- Update internal imports
- Update: manifest, runtime-topology.yaml, TOPOLOGY-DAG.md, SVGs (~15 refs)
- Update manifest type from "api-service" (already correct type, just fixing name)
- Re-install venv

### Phase 2: One external dependency to fix

**4. market-tick-data-handler -> market-tick-data-service**

- Rename directory + GitHub
- Rename Python package: `market_tick_data_handler/` -> `market_tick_data_service/`
- Update self pyproject.toml: `name = "market-tick-data-service"`
- Update internal imports
- Fix external dep: `execution-service/pyproject.toml` line 13 references `market-data-tick-handler` (note: already misspelled as "market-data-tick-handler" not "market-tick-data-handler")
- Update `[tool.uv.sources]` path: `{ path = "../market-tick-data-service" }`
- Update: manifest, runtime-topology.yaml, sharding.market-tick-data-handler.yaml (rename file too), codex docs, SVGs
- Re-install: both market-tick-data-service AND execution-service venvs

**5. execution-service -> execution-service**

- Rename directory + GitHub
- Rename Python package: `execution_service/` -> `execution_service/`
- Update self pyproject.toml
- Update ALL internal imports (many files)
- Update: manifest, runtime-topology.yaml, sharding.execution-service.yaml (rename file), codex docs, SVGs, cursor rules (~30 refs)
- Fix the MTDH dep path from step 4 (now points to `../execution-service` not `../execution-service`)
- Re-install venv

### Phase 3: Large cross-repo rename

**6. api-contracts -> unified-api-contracts**

- Rename directory + GitHub: `mv api-contracts unified-api-contracts`
- Rename Python package directory: `api_contracts/` -> `unified_api_contracts/`
- Also rename sub-package if exists: `api_contracts_external/` -> check if it should also be renamed or if it's under `api_contracts/`
- Update self pyproject.toml: `name = "unified-api-contracts"`
- Update 17+ pyproject.toml files across workspace: change `"api-contracts>=..."` to `"unified-api-contracts>=..."`
- Update 17+ `[tool.uv.sources]` sections: `api-contracts = { path = "../api-contracts" }` -> `unified-api-contracts = { path = "../unified-api-contracts" }`
- Update 8+ repos with Python imports: `from api_contracts` -> `from unified_api_contracts`
- Update cursor rules: `.cursor/rules/external-import-standards.mdc`, `api-contracts-version-alignment.mdc`, `api-contracts-usage.mdc` (rename rule files too)
- Update codex docs: TOPOLOGY-DAG.md, SSOT-INDEX, contracts-integration.md, api-contracts-chain.md
- Update all SVGs, manifest, runtime-topology.yaml
- Re-install venvs in ALL 17+ dependent repos

### Phase 4: Verification

- Run `xmllint --noout` on both SVGs
- Verify `uv pip install -e ".[dev]"` succeeds in all renamed repos
- Verify `python -c "from unified_api_contracts import ..."` works
- Update consolidated_remaining_work.plan.md to mark rename todos as done

## Files affected (comprehensive list)

### Per-rename manifest + config updates

- `unified-trading-pm/workspace-manifest.json` -- all 6 repo entries + dependency references + topologicalOrder
- `unified-trading-deployment-v3/configs/runtime-topology.yaml` -- service names in flows, sharding, deployment modes, health probes, etc.
- `unified-trading-deployment-v3/configs/sharding.*.yaml` -- rename 3 files (market-tick-data-handler, execution-service, alerting-service -> new names)
- `unified-trading-deployment-v3/configs/checklist.*.yaml` -- rename 3 files
- `unified-trading-deployment-v3/configs/data-catalogue.*.yaml` -- rename affected files

### SVGs to rebuild

- `unified-trading-codex/04-architecture/WORKSPACE_MANIFEST_DAG.svg`
- `unified-trading-codex/04-architecture/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg`
- `unified-trading-codex/04-architecture/TARGET_DAG_CLEAN.svg` (if exists)

### Codex docs

- `unified-trading-codex/04-architecture/TOPOLOGY-DAG.md` -- mermaid node names and labels
- `unified-trading-codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` -- service name references
- `unified-trading-codex/00-SSOT-INDEX.md` -- references
- `unified-trading-codex/05-infrastructure/unified-libraries/INTERNAL_DEPENDENCY_GRAPH.md`
- `unified-trading-codex/05-infrastructure/UI-DEPENDENCY-MATRIX.md`

### Cursor rules

- `.cursor/rules/external-import-standards.mdc` -- api-contracts import examples
- `.cursor/rules/dag-enforcement.mdc` -- service name examples
- `unified-trading-pm/cursor-rules/api-contracts-version-alignment.mdc` -- rename file
- `unified-trading-pm/cursor-rules/api-contracts-usage.mdc` -- rename file
- `unified-trading-pm/cursor-rules/external-import-standards.mdc`

### Plan

- `.cursor/plans/consolidated_remaining_work.plan.md` -- update all references to renamed repos

## Risk mitigation

- Do renames in dependency order (no deps first, most deps last)
- After each rename, verify the repo's own tests still import correctly
- api-contracts rename is the riskiest -- do it last, verify each consumer repo individually
- Keep old Python package as a re-export shim temporarily if needed (but prefer clean break per delete-deprecated.mdc)
