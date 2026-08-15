---
doc_type: plan
title: operational-config-migration
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-11'
overview: Migrate all operational configs from deployment-service/configs/ to unified-trading-pm/configs/ to eliminate cross-service dependency in deployment-api
type: infra
epic: epic-infra
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C0, deployment: none, business: none, readiness_note: Receives migrated YAML config files}
- {repo: deployment-service, code: C0, deployment: none, business: none, readiness_note: 'Replaces moved files with PM symlinks, deletes dead checklist templates'}
- {repo: deployment-api, code: C0, deployment: none, business: none, readiness_note: Switches from configs/ (→deployment-service) to pm-configs/ (→unified-trading-pm)}
depends_on: []
todos:
- {id: move-configs-to-pm, content: Copy all operational YAML configs from deployment-service/configs/ to unified-trading-pm/configs/, status: done, note: 'DONE — All YAML files + services/ directory moved. Commit: TBD'}
- {id: deployment-service-symlinks, content: 'Replace moved files in deployment-service/configs/ with symlinks to ../../unified-trading-pm/configs/, delete dead checklist.template.*.yaml', status: done, note: 'DONE — All 51 symlinks subsequently REMOVED (backward compat approach rejected). deployment-service/configs/ is now clean. Commit: af31e2e'}
- {id: deployment-api-symlink, content: 'Create deployment-api/pm-configs symlink → ../unified-trading-pm/configs, remove old configs symlink', status: done, note: 'DONE — pm-configs symlink added, configs symlink removed'}
- {id: update-get-config-dir, content: Update get_config_dir() in service_utils.py and app_config.py to search pm-configs/ (bundled) then ../unified-trading-pm/configs (sibling), status: done, note: DONE — Both functions updated with two-phase search (bundled → sibling)}
- {id: update-tests, content: Update test_app_config.py to use pm-configs instead of configs, status: done, note: 'DONE — TestGetConfigDir uses pm-configs dir, error message updated'}
- {id: update-cloudbuild, content: Update deployment-api/cloudbuild.yaml fetch-readiness-data step to also copy pm-configs/ from unified-trading-pm clone, status: done, note: DONE — pm-configs/ populated from /tmp/unified-trading-pm/configs/}
- {id: update-dockerfile, content: Add COPY pm-configs/ ./pm-configs/ to deployment-api Dockerfile (both api and api-dev stages via base), status: done, note: DONE — COPY pm-configs/ added to api stage}
- {id: quality-gates, content: Run bash scripts/quality-gates.sh in deployment-api — all tests must pass, status: done, note: 'DONE — All tests pass, coverage maintained'}
- {id: remove-backward-compat-symlinks, content: 'Remove all 51 backward-compat symlinks from deployment-service/configs/ — clean migration, no transitional shims', status: done, note: 'DONE — git rm of all symlinks. Commit: af31e2e (deployment-service)'}
- {
    id: update-code-references,
    content: Update all deployment-service/configs/ path references in Python/YAML source files to unified-trading-pm/configs/,
    status: done,
    note: 'DONE — instruments-service catalogue_updater.py + CI workflow (c12c35e, 824e723); strategy-service cascade_subscriber.py (07e1044); system-integration-tests error string (3a41740); deployment-api docstrings (3ba90bf)',
    verified:
      '2026-08-15 VERIFIED (review, slot 3, per measurement-claims-discipline — confirmed via gh api commit lookup
      against instruments-service on GitHub, not a local-workspace-absence assumption; the local shallow clone was
      inconclusive per the audit that flagged this): the DONE (c12c35e, 824e723) claim is ACCURATE. Commit c12c35e
      (pre-history-rewrite SHA — this repo underwent a documented history rewrite 2026-08-05; the identical change
      is reachable post-rewrite as 9e752677d4, same date/message) genuinely modified
      instruments_service/catalogue_updater.py + pyproject.toml (2026-03-11T21:41:12Z, "fix: update catalogue path
      to unified-trading-pm/configs/"); commit 824e723 genuinely modified .github/workflows/quality-gates.yml the
      same day. catalogue_updater.py itself was CREATED 2026-03-08 (724990c60e, "feat(catalogue): add
      catalogue_updater post-batch hook") and later REMOVED — not renamed (previous_filename: null) — 2026-03-24 by
      commit 29f34ff083 ("feat: production-ready instruments-service ... per-bucket ManifestWriter catalogue ..."),
      which deleted both catalogue_updater.py and its test file as part of a documented architectural refactor
      superseding it with a ManifestWriter-based catalogue. The workspace absence today is
      CONFIRMED-BUILT-THEN-SUPERSEDED-VIA-REFACTOR, not fabrication. No correction to the done-claim itself is
      needed.',
  }
- {id: clean-ssot-docs, content: 'Remove all backward-compat symlink language from SSOT docs (00-SSOT-INDEX.md, 10-audit/README.md)', status: done, note: 'DONE — 4 backward-compat references removed from codex. Commit: 009e823 (unified-trading-codex)'}
- {id: update-gha-path-triggers, content: 'Update GHA workflow paths: triggers in sync-check.yml, epic-alignment-check.yml, weekly-sync.yml to point to unified-trading-pm/configs/', status: done, note: 'DONE — All 3 workflow files updated. Commit: 20ca23e (unified-trading-codex)'}
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
