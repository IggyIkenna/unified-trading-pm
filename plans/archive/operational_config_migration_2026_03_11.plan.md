---
name: operational-config-migration
overview:
  Migrate all operational configs from deployment-service/configs/ to unified-trading-pm/configs/ to eliminate
  cross-service dependency in deployment-api
type: infra
epic: epic-infra
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
    readiness_note: "Receives migrated YAML config files"
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
    readiness_note: "Replaces moved files with PM symlinks, deletes dead checklist templates"
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
    readiness_note: "Switches from configs/ (→deployment-service) to pm-configs/ (→unified-trading-pm)"

depends_on: []

todos:
  - id: move-configs-to-pm
    content: "Copy all operational YAML configs from deployment-service/configs/ to unified-trading-pm/configs/"
    status: done
    note: "DONE — All YAML files + services/ directory moved. Commit: TBD"
  - id: deployment-service-symlinks
    content:
      "Replace moved files in deployment-service/configs/ with symlinks to ../../unified-trading-pm/configs/, delete
      dead checklist.template.*.yaml"
    status: done
    note: "DONE — Symlinks created, dead templates deleted. Commit: TBD"
  - id: deployment-api-symlink
    content: "Create deployment-api/pm-configs symlink → ../unified-trading-pm/configs, remove old configs symlink"
    status: done
    note: "DONE — pm-configs symlink added, configs symlink removed"
  - id: update-get-config-dir
    content:
      "Update get_config_dir() in service_utils.py and app_config.py to search pm-configs/ (bundled) then
      ../unified-trading-pm/configs (sibling)"
    status: done
    note: "DONE — Both functions updated with two-phase search (bundled → sibling)"
  - id: update-tests
    content: "Update test_app_config.py to use pm-configs instead of configs"
    status: done
    note: "DONE — TestGetConfigDir uses pm-configs dir, error message updated"
  - id: update-cloudbuild
    content:
      "Update deployment-api/cloudbuild.yaml fetch-readiness-data step to also copy pm-configs/ from unified-trading-pm
      clone"
    status: done
    note: "DONE — pm-configs/ populated from /tmp/unified-trading-pm/configs/"
  - id: update-dockerfile
    content: "Add COPY pm-configs/ ./pm-configs/ to deployment-api Dockerfile (both api and api-dev stages via base)"
    status: done
    note: "DONE — COPY pm-configs/ added to api stage"
  - id: quality-gates
    content: "Run bash scripts/quality-gates.sh in deployment-api — all tests must pass"
    status: done
    note: "DONE — All tests pass, coverage maintained"

isProject: false
---

# Plan: Operational Config Migration — deployment-service → unified-trading-pm

## Problem

`deployment-api/configs` is a symlink to `../deployment-service/configs`. This creates two violations:

1. **Cross-service dependency**: deployment-api depends directly on deployment-service source files. Services must never
   consume each other's source repos — only PM and codex are valid shared sources via clone.
2. **Docker build context break**: The symlink target is outside the deployment-api Docker build context.
   `COPY codex-data/` and `COPY pm-plans/` work because cloudbuild pre-populates them as real directories. But
   `configs/` is never populated — all routes using `app.state.config_dir` fail silently at Cloud Run startup.

## Architecture Rule Violated

> PM = SSOT for workspace config data (manifest, plans, operational configs) codex = SSOT for standards and readiness
> data Services never depend on each other's source repos

`runtime-topology.yaml` in deployment-service/configs already demonstrates the correct pattern: it's a symlink to
`../../unified-trading-pm/configs/runtime-topology.yaml`. All other operational configs should follow the same pattern.

## Solution

1. **PM becomes SSOT** for all operational YAML configs (sharding, dependencies, start dates, venues, data catalogues,
   etc.)
2. **deployment-service/configs/** becomes symlinks only — pointing to `../../unified-trading-pm/configs/`
3. **deployment-api** reads from `pm-configs/` (the new bundled dir name) instead of `configs/`
4. **cloudbuild.yaml** populates `pm-configs/` from the PM clone (same pattern as `codex-data/` and `pm-plans/`)
5. **Dockerfile** adds `COPY pm-configs/ ./pm-configs/`

## Files Moved from deployment-service/configs/ to unified-trading-pm/configs/

### Operational YAML configs (read by deployment-api routes):

- `sharding_config.yaml`
- `dependencies.yaml`
- `expected_start_dates.yaml`
- `bucket_config.yaml`
- `cloud-providers.yaml`
- `credentials-registry.yaml`
- `data-providers.yaml`
- `protocol-config-schema.yaml`
- `representative_instruments.yaml`
- `checklist.prerequisites.yaml`
- `PARADISE_WORKFLOW.yaml`
- All `data-catalogue.*.yaml` (15 files)
- All `sharding.*.yaml` (16 files)
- `services/` directory (16 service subdirs with batch.env / live.env)

### Dead files deleted (not moved):

- `checklist.template.service.yaml`
- `checklist.template.api-service.yaml`
- `checklist.template.library.yaml`
- `checklist.template.ui.yaml` (All 41 checklist items are captured in codex v3.0 SSOT — these templates are unused)

### Kept in deployment-service/configs/ (deployment-service specific):

- `runtime-topology.yaml` (already a symlink to PM — unchanged)
- `RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.dot`, `.svg`, `RUNTIME_TOPOLOGY_DECISIONS.md` (generated docs)
- `generate_topology_svg.py`, `in_memory_tick_queue.py` (deployment-service scripts)
- `README.md`, `BUCKET_CONFIG_SCHEMA.md` (documentation)
