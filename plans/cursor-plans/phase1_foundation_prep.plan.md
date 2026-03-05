---
name: Phase 1 — Foundation & Prep
overview: |
  Foundation and prep work that MUST complete before any library/service tier work (Phase 2) can start.
  Three parallel streams: STREAM A (CI/CD infrastructure), STREAM B (deployment structure refactor),
  STREAM C (quality gate baseline audit). No quickmerge runs until STREAM A is complete.
  Phase 1 is complete when: all 55 repos have quickmerge + commit-msg hook; CI/CD pipeline live;
  deployment structure refactored (UTD V3 split, visualizer-ui/api extracted, system-integration-tests repo);
  SSOT docs clean; naming consistent.
todos:
  - id: p1-naming-cleanup-done
    content: "DONE (2026-02-28): Global naming cleanup across deployment-v3/configs, unified-trading-codex active docs, consolidated plan. Replaced: market-tick-data-handler→market-tick-data-service (~50+ hits), alerting-service→alerting-service, client-reporting-api→client-reporting-api, position-balance-monitor→position-balance-monitor-service (bare form only). .cursor/rules and workspace-manifest.json were already clean."
    status: completed
  - id: p1-ssot-docs-done
    content: "DONE (2026-02-28): SSOT doc alignment complete: (1) 00-SSOT-INDEX.md updated with WORKSPACE_MANIFEST_DAG.svg and RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg rows + archived diagram supersession notes; (2) LIBRARY-DEPENDENCY-MATRIX.md already had correct scope header; (3) Created 04-architecture/api-services-cluster.md; (4) Created 06-coding-standards/ui-service-separation.md; (5) Created 08-workflows/service-pair-flows.md; (6) dag-tier-corrections: URDI=T0, UDC=T3, EAL=T0, MEL=T0 all verified correct in codex + manifest; lib-phase5-t2-quality-gates fixed to exclude URDI."
    status: completed
  - id: ci-dag-validation
    content: "STEP A0 — DAG VALIDATION [BLOCKING precondition]: Verify workspace-manifest.json arch_tier fields match canonical DAG. Verify no tier violations in pyproject.toml dependencies. Cursor rule dag-enforcement.mdc must be in place. Todos: dag-ssot-align (reconcile manifest+topology docs), dag-tier-corrections (already done), dag-orphan-repos-manifest (4 missing API service repos), dag-mel-tier-mismatch (fix MEL visual bug in SVG)."
    status: pending
  - id: ci-quickmerge-rollout
    content: "STEP A1 — QUICKMERGE + VERSION-BUMP TO ALL 55 REPOS [BLOCKING — do before anything else] [10 agents PARALLEL]: Push updated quickmerge.sh template AND version-bump.yml to ALL 55 repos simultaneously. Each agent handles 5-6 repos: (1) Copy quickmerge template → scripts/quickmerge.sh; (2) Copy version-bump.yml → .github/workflows/version-bump.yml; (3) Verify pyproject.toml exists with version field; (4) git commit 'chore: sync quickmerge template + version-bump workflow' → git push. Version-bump.yml SSOT: unified-trading-pm/.github/workflows/version-bump.yml. Nothing else starts until all 55 repos have both templates."
    status: pending
  - id: ci-commit-msg-hooks
    content: "STEP A2 — COMMIT-MSG HOOKS [4 agents PARALLEL, after A1]: Add commit-msg hook validating feat:/fix:/chore:/BREAKING CHANGE: prefix to all 55 repos. Also: ci-ar-local-version-verification (GCP AR accepts PEP 440 local (+) versions), ci-refactor-scope-manifest (add refactor_scope to workspace-manifest), ci-versions-reset-pyproject (verify all pyproject.toml versions are 0.x.x)."
    status: pending
  - id: ci-pipeline-wiring
    content: "STEP A3 — CI/CD PIPELINE [3 agents PARALLEL, after A2]: ci-github-actions-dep-branch-clone (${DEP_BRANCH:-main} + git ls-remote fallback in all quality-gates.yml); ci-cloud-build-feature-branch-trigger + ci-cloud-build-feature-version-inject; ci-auto-version-bump-github-action (GH Action bumps version on main merge from commit prefix). Then after Stream B: ci-temp-manifest-schema."
    status: pending
  - id: arch-visualizer-extract
    content: "ACTIVE VIOLATION: Extract execution-service embedded UI/API: (1) execution-service/visualizer-ui/ → new repo execution-visualizer-ui; (2) execution-service/visualizer-api/ → merge into execution-results-api or new execution-visualizer-api repo; (3) delete both dirs from execution-service; (4) update cloudbuild.yaml. Task: arch-exec-services-visualizer-extract."
    status: pending
  - id: arch-deployment-split
    content: "Split unified-trading-deployment-v3 into 4 repos: (1) deployment-service/ — Python package (orchestrator, catalog, config_loader, cli, cloud_client, monitor, shard_builder, shard_calculator, backends/), terraform/, configs/ (YAML checklists, bucket configs). Move smoke_test_framework.py → tests/integration/shard_smoke/. Split orchestrator.py (672L) and config_loader.py (551L) by SRP before extract; (2) deployment-api/ — thin FastAPI, imports deployment-service, GoogleOAuthMiddleware on write endpoints, port 8001; (3) deployment-ui/ — React UI calling deployment-api, OAuth ADMIN scope, SSE for status (scaffolded already); (4) system-integration-tests/ — NEW repo (per new-repo-setup.md), Layer 3a + 3b. Layer 2 (infra verification) lives in deployment-service/scripts/verify_infra.py. Tasks: deployment-v3-four-way-split, arch-deployment-v3-ui-extract."
    status: pending
  - id: arch-ui-audit-full
    content: "Full audit of all service repos for embedded UI: check for ui/, frontend/, static/, visualiz*, *.tsx, *.jsx, package.json, index.html inside Python service repos. Known violations: execution-service (visualizer-ui + visualizer-api), unified-trading-deployment-v3 (ui/). Check also: alerting-service, market-data-processing-service, client-reporting-api, risk-and-exposure-service. Task: ui-service-separation-audit-full."
    status: pending
  - id: integration-system-tests-repo
    content: "Create system-integration-tests repo per new-repo-setup.md: Layer 3a (fast smoke @pytest.mark.smoke, <5 min) + Layer 3b (full @pytest.mark.full_e2e, 15-30 min). Sequential: 3a must pass before 3b. Zero Python imports from services — HTTP/GCS/PubSub interaction only. SSOT: 06-coding-standards/integration-testing-layers.md. Tasks: integration-system-integration-tests-repo, integration-layer3-implement."
    status: pending
  - id: integration-layer2-infra-verify
    content: "Add verify_infra.py to deployment-service/scripts/ after four-way split: checks GCS buckets exist + IAM, PubSub topics exist + subscriptions, Secret Manager entries exist. Exposed as GET /infra/health in deployment-api. Gates deployment success before Layer 3. Task: integration-layer2-infra-verify."
    status: pending
  - id: infra-merge-utdv3
    content: "ibkr-gateway-infra/ dir (workspace root) contains ibkr-gateway-infra/ibkr-gateway/ Terraform config (main.tf, variables.tf). Move: ibkr-gateway-infra/ibkr-gateway/ → unified-trading-deployment-v3/infra/ibkr-gateway/ then delete ibkr-gateway-infra/. Update manifest. Task: infra-merge-utdv3."
    status: pending
  - id: hybrid-live-seam
    content: "Implement/document hybrid live in-memory adapter seam for MDPS←MTDH (allowed ONLY under co_located_vm deployment profile per runtime-topology.yaml). Task: hybrid-live-seam."
    status: pending
  - id: ci-cloud-agnostic-rule
    content: "Create .cursor/rules/cloud-agnostic.mdc: RULE: All cloud I/O goes through get_storage_client(), get_secret_client(), GCSEventSink — never direct google-cloud-* or boto3. CLOUD_PROVIDER env var switches provider. Test both paths in test_cloud_agnostic_paths.py. GCP primary; AWS secondary. Reference cloud-agnostic-migration.md. Task: aws-migration-cursor-rule."
    status: pending
  - id: ci-dag-enforcement-rule
    content: "Create .cursor/rules/dag-enforcement.mdc: RULE enforcing DAG tier boundaries — no T2 importing T3+, no service importing another service, no UI importing from service engine. CI check validates pyproject.toml dependencies against workspace-manifest.json arch_tier fields. Task: arch-dag-enforcement-cursor-rule."
    status: pending
  - id: ci-ui-separation-rule
    content: "Create .cursor/rules/ui-service-separation.mdc (if not already present): RULE: UI code must NEVER live inside a service repo. Known violations tracked in arch-exec-services-visualizer-extract and arch-deployment-v3-ui-extract. Task: arch-ui-separation-rule."
    status: pending
  - id: ci-manifest-status
    content: "Add ci_status, quality_gate_status, coverage_pct, bypass_audit_path, testing_level, skipped_gates fields to workspace-manifest.json for all repos. Current state: NO_STATUS for 40/57. Task: ci-manifest-status-fields."
    status: pending
  - id: ci-add-missing-quality-gates
    content: "Add quality-gates.sh to 12 repos missing it: unified-api-contracts, unified-events-interface, unified-reference-data-interface, alerting-service, unified-trade-execution-interface, features-calendar-service, unified-position-interface, unified-trading-services, ml-training-service, ml-inference-service, client-reporting-api, pnl-attribution-service. Use codex template (06-coding-standards/quality-gates-library-template.sh or service template). [10 agents, 1-2 repos each]. Task: ci-quality-gates-missing-repos."
    status: pending
  - id: ci-qg-baseline-run
    content: "DONE (2026-03-05): Created run-qg-baseline.sh. Run: bash unified-trading-pm/scripts/run-qg-baseline.sh. Run quality gates baseline on all 30 repos that have quality-gates.sh. Record pass/fail + coverage % + bypass count per repo into workspace-manifest.json ci_status fields. Use 4 parallel agents (8 repos each). This is the baseline snapshot needed before any hardening work. Task: ci-per-repo-status-run (baseline only)."
    status: pending
  - id: ci-cloudbuild-audit
    content: "Verify all 29 cloudbuild.yaml files actually invoke quality-gates.sh inside the Docker image (not just run pytest standalone). Per cloud-build-test-in-image.mdc: tests run INSIDE the built image. Audit each for: docker build → docker run quality-gates.sh --no-fix --quick → docker push. Fix any that run pytest or ruff outside the image. [5 agents, 6 repos each]. Task: ci-cloudbuild-quality-gate-wire."
    status: pending
  - id: ci-aws-parity
    content: "AWS parity tasks [3 agents PARALLEL]: aws-compute-stubs-wire (verify aws_batch.py + aws_ec2.py match cloud_run.py interface), aws-secret-naming-parity (mirror GCP SM naming in AWS SM), aws-cloudbuild-parity (add buildspec.aws.yaml to all repos with cloudbuild.yaml)."
    status: pending
isProject: true
---

# Phase 1 — Foundation & Prep

> **Gate:** Phase 2 (Library & Service Tier hardening) MUST NOT start until all Phase 1 DONE criteria are met.
> No `quickmerge` runs on library/service repos until STREAM A (CI/CD) is fully complete.

---

## NAMING CHANGE MANDATE — Zero Technical Debt

> **SSOT for repo names:** `unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg` (57 repos, 11 levels, generated from `workspace-manifest.json`).
> **SSOT for runtime topology:** `unified-trading-deployment-v3/configs/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg`.
> Any name not matching these diagrams is WRONG and must be fixed at EVERY level below.

When any component is renamed, the change is **complete** only when ALL of the following are updated. No shortcuts, no aliases, no backward compatibility shims.

| Level                                 | What to Change                                                                                                                                  |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **GitHub repo name**                  | Rename via GitHub settings; update all links                                                                                                    |
| **Artifact Registry**                 | Rename GCP AR package; update all `cloudbuild.yaml` publisher + consumer `--tag` lines                                                          |
| **CI/CD triggers**                    | Cloud Build trigger name must match repo name; update `version-bump.yml` `push:` branch filters                                                 |
| `**pyproject.toml`\*\*                | `[project] name` field; all `[project.dependencies]` entries in dependent repos                                                                 |
| **Python package dir**                | Rename `market_tick_data_handler/` → `market_tick_data_service/`; update `__init__.py`                                                          |
| **All imports**                       | `from market_tick_data_handler import ...` → `from market_tick_data_service import ...` across ALL 57 repos (run `rg` to find every occurrence) |
| `**workspace-manifest.json`\*\*       | `name`, `github_url`, `artifact_registry_url`, `package_name` — all 4 fields                                                                    |
| `**runtime-topology.yaml**`           | All service name references                                                                                                                     |
| **Deployment checklists**             | `unified-trading-deployment-v3/configs/checklist.*.yaml`                                                                                        |
| `**RUNTIME_TOPOLOGY_DECISIONS.md`\*\* | All narrative references                                                                                                                        |
| **Cursor rules**                      | Any `.cursor/rules/*.mdc` mentioning old name (`rg` search)                                                                                     |
| **Codex docs**                        | All `unified-trading-codex/**/*.md` mentioning old name (`rg` search)                                                                           |
| **Docker image tags**                 | `gcr.io/…/<old-name>:$TAG` → `gcr.io/…/<new-name>:$TAG`                                                                                         |
| **Cloud Run service name**            | Requires redeploy + deletion of old Cloud Run service                                                                                           |
| **PubSub topics**                     | Any topic named after old service → rename + update all publishers/subscribers                                                                  |
| **Secret Manager**                    | Any secrets keyed to old service name                                                                                                           |
| **Environment variables**             | `SERVICE_NAME`, `APP_NAME`, any env var using old name                                                                                          |
| **Phase plans + PM docs**             | This plan and all `unified-trading-pm/plans/` docs                                                                                              |

### NEVER (no exceptions)

- Leave old name as import alias, re-export, or `_deprecated.py`
- Use `try/except ImportError` to fall back to old name
- Keep both old and new `pyproject.toml` entries "for safety"
- Commit name change to one repo without simultaneously updating all consumers (`--dep-branch` handles this)

### Current Known Renames (SSOT as of 2026-02-28)

| Old Name                         | Canonical Name                     | Scope                              |
| -------------------------------- | ---------------------------------- | ---------------------------------- |
| `market-tick-data-handler`       | `market-tick-data-service`         | All levels                         |
| `client-reporting-api`           | `client-reporting-api`             | All levels                         |
| `alerting-service`               | `alerting-service`                 | All levels                         |
| `position-balance-monitor`       | `position-balance-monitor-service` | All levels                         |
| `ml-training-ui`                 | `ml-training-ui`                   | All levels                         |
| `execution-analytics-ui`         | `execution-analytics-ui`           | All levels (repo renamed/replaced) |
| `market_tick_data_handler` (pkg) | `market_tick_data_service`         | Python imports                     |
| `client_reporting_api` (pkg)     | `client_reporting_api`             | Python imports                     |

Stream A `ci-quickmerge-rollout` and `ci-commit-msg-hooks` tasks MUST include verifying none of the old names above appear in `pyproject.toml`, `cloudbuild.yaml`, or `quality-gates.sh` in each repo.

---

## Agent Bootstrap

Every sub-agent launched from this plan must start with:

```bash
# 1. Activate workspace venv
source /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.venv-workspace/bin/activate
which python  # must be .venv-workspace/bin/python
which ruff    # must be .venv-workspace/bin/ruff

# 2. Verify tools
python --version  # must be 3.13.x
basedpyright --version  # workspace basedpyright

# 3. Follow all workspace cursor rules in .cursorrules
# uv not pip | quickmerge not git push | basedpyright <dir>/ not basedpyright .
# delete deprecated code | no parallel code paths | no summary docs
```

---

## Phase Ordering

```
Phase 1 (this plan)      →  Phase 2 (library/service tier)  →  Phase 3 (hardening + ML)
Foundation & Prep           Tier hardening + library upgrades    Quality gates + production
ALL STREAMS must finish     Requires: quickmerge live on all 55   Requires: Phase 2 complete
```

**Why Phase 1 first:**

- `quickmerge` must exist on all 55 repos before any feature branch work starts (A1)
- Commit-msg hooks must be in place before any commits are made for Phase 2 (A2)
- CI/CD dep-branch clone must work before cross-repo dependency cascades (A3)
- Deployment structure must be clean before service tier work references it (B)
- QG baseline must be recorded before hardening so we can measure improvement (C)

---

## Stream Execution Diagram

```
TIME ──────────────────────────────────────────────────────────────────►

STREAM A   [A0: DAG Validation]──[A1: Quickmerge Rollout (55 repos)]
(CI/CD)                                    │
BLOCKING                          [A2: Commit-Msg Hooks (55 repos)]
                                           │
                                  [A3: CI/CD Pipeline Wiring]
                                           │
                              ════════ STREAM A COMPLETE ════════
                                           │
                                    (Phase 2 unblocked)

STREAM B   [arch-visualizer-extract]────────────────────────────────────┐
(Deploy     [arch-deployment-split]─────────────────────────────────────┤
Structure)  [arch-ui-audit-full]────────────────────────────────────────┤
PARALLEL    [integration-system-tests-repo]─────────────────────────────┤
with A      [integration-layer2-infra-verify]───────────────────────────┤
            [infra-merge-utdv3]─────────────────────────────────────────┤
            [hybrid-live-seam]──────────────────────────────────────────┘
                              ════════ STREAM B COMPLETE ════════

STREAM C   [ci-cloud-agnostic-rule]─────────────────────────────────────┐
(QG         [ci-dag-enforcement-rule]───────────────────────────────────┤
Baseline)   [ci-ui-separation-rule]─────────────────────────────────────┤
PARALLEL    [ci-manifest-status]────────────────────────────────────────┤
with A+B    [ci-add-missing-quality-gates]──────────────────────────────┤
            [ci-qg-baseline-run]────────────────────────────────────────┤
            [ci-cloudbuild-audit]───────────────────────────────────────┤
            [ci-aws-parity]─────────────────────────────────────────────┘
                              ════════ STREAM C COMPLETE ════════
```

**Parallelism rules:**

- STREAM A, B, C run in parallel with each other
- Within STREAM A: A0 → A1 → A2 → A3 (strictly sequential, each blocks the next)
- Within STREAM B: all items run in parallel (independent repos/dirs)
- Within STREAM C: all items run in parallel (independent rule/audit tasks)

---

## Stream A — CI/CD (BLOCKING)

The most critical stream. Nothing in Phase 2 starts until A3 is complete.

### A0 — DAG Validation (precondition for A1)

Verify `workspace-manifest.json` `arch_tier` fields match the canonical DAG before any rollout.
Four sub-tasks:

- `dag-ssot-align`: reconcile manifest + topology docs
- `dag-orphan-repos-manifest`: 4 API service repos missing from manifest
- `dag-mel-tier-mismatch`: fix MEL visual bug in SVG (shows wrong tier)
- Cursor rule `dag-enforcement.mdc` must be created (see Stream C)

### A1 — Quickmerge + Version-Bump Rollout (10 agents, 55 repos)

**Nothing else starts until this completes.**

Each agent handles 5–6 repos:

1. Copy `scripts/quickmerge.sh` from SSOT: `unified-trading-pm/scripts/quickmerge.sh`
2. Copy `.github/workflows/version-bump.yml` from SSOT: `unified-trading-pm/.github/workflows/version-bump.yml`
3. Verify `pyproject.toml` has `version` field
4. `git commit 'chore: sync quickmerge template + version-bump workflow'` → `git push`

### A2 — Commit-Msg Hooks (4 agents, 55 repos, after A1)

Add `commit-msg` hook to `.git/hooks/commit-msg` (or pre-commit config) in all 55 repos.
Hook validates prefix: `feat:|fix:|chore:|docs:|refactor:|test:|ci:|BREAKING CHANGE:`
Additional sub-tasks run in parallel:

- `ci-ar-local-version-verification`: confirm GCP AR accepts PEP 440 `+local` versions
- `ci-refactor-scope-manifest`: add `refactor_scope` field to workspace-manifest schema
- `ci-versions-reset-pyproject`: all repos must be `0.x.x` (no pre-bumped versions)

### A3 — CI/CD Pipeline Wiring (3 agents, after A2)

Three parallel sub-tasks:

1. **dep-branch clone**: `${DEP_BRANCH:-main}` + `git ls-remote` fallback in all `quality-gates.yml`
2. **Cloud Build feature trigger**: feature branch trigger + version inject (`+feat.BRANCH_SHA`)
3. **GH Action version bump**: reads squash-merge commit prefix → bumps semver on main merge

---

## Stream B — Deployment Structure (parallel with A)

### arch-visualizer-extract (ACTIVE VIOLATION)

`execution-service` embeds a full React UI and a FastAPI backend. These violate `ui-service-separation.md`.

Steps:

1. `execution-service/visualizer-ui/` → new repo `execution-visualizer-ui`
2. `execution-service/visualizer-api/` → merge into `execution-results-api` OR new `execution-visualizer-api`
3. Delete both dirs from `execution-service`
4. Update `execution-service/cloudbuild.yaml`
5. Update `workspace-manifest.json`

### arch-deployment-split (four-way split of unified-trading-deployment-v3)

| New Repo                   | Contents                                                                                                                                           | Tier                |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| `deployment-service`       | Python package: orchestrator, catalog, config_loader, cli, cloud_client, monitor, shard_builder, shard_calculator, backends/, terraform/, configs/ | **merge_level: 6**  |
| `deployment-api`           | Thin FastAPI; imports deployment-service; GoogleOAuthMiddleware on write endpoints; port 8001                                                      | **merge_level: 6**  |
| `deployment-ui`            | React UI → deployment-api; OAuth ADMIN scope; SSE for status (scaffolded)                                                                          | **merge_level: 9**  |
| `system-integration-tests` | NEW repo; Layer 3a (smoke, <5 min) + Layer 3b (full e2e, 15–30 min)                                                                                | **merge_level: 10** |

Pre-split: split `orchestrator.py` (672 L) and `config_loader.py` (551 L) by SRP before extract.

> **Tier note (2026-02-28):** Merge levels assigned in workspace-manifest.json tier restructure. `unified-trading-deployment-v3` (the monorepo being split) → merge_level: 10 (IaC; deploy last, references all service images). deployment-api/engine at L6 = own tier between foundational services (L5) and bulk services (L7).

Layer 2 infra verification: `deployment-service/scripts/verify_infra.py` → exposed as `GET /infra/health`.

### arch-ui-audit-full

Full sweep of all 17 service repos for embedded UI artifacts:

- Patterns: `ui/`, `frontend/`, `static/`, `visualiz`_, `_.tsx`, `\*.jsx`, `package.json`, `index.html`
- Known violations: `execution-service`, `unified-trading-deployment-v3`
- Also check: `alerting-service`, `market-data-processing-service`, `client-reporting-api`, `risk-and-exposure-service`

### integration-system-tests-repo

New repo `system-integration-tests` (per `new-repo-setup.md`):

- Layer 3a: `@pytest.mark.smoke`, <5 min, must pass before 3b
- Layer 3b: `@pytest.mark.full_e2e`, 15–30 min
- Zero Python imports from services — HTTP/GCS/PubSub interaction only
- SSOT: `06-coding-standards/integration-testing-layers.md`

### infra-merge-utdv3

`ibkr-gateway-infra/ibkr-gateway/` (Terraform) → `unified-trading-deployment-v3/infra/ibkr-gateway/`
Then delete `ibkr-gateway-infra/` from workspace root. Update manifest.

### hybrid-live-seam

Document + implement in-memory adapter seam for `MDPS←MTDH`.
Allowed ONLY under `co_located_vm` deployment profile (see `runtime-topology.yaml`).

---

## Stream C — QG Baseline Audit (parallel with A and B)

### Cursor Rules to Create

| Rule file                   | Purpose                                                                      |
| --------------------------- | ---------------------------------------------------------------------------- |
| `cloud-agnostic.mdc`        | All cloud I/O via abstraction layer; CLOUD_PROVIDER env var; test both paths |
| `dag-enforcement.mdc`       | Enforce tier boundaries; CI validates pyproject.toml vs manifest arch_tier   |
| `ui-service-separation.mdc` | UI code must never live inside a service repo                                |

### Manifest Schema Extension

Add to `workspace-manifest.json` for every repo:

```yaml
ci_status: PASSING | FAILING | NO_STATUS
quality_gate_status: PASSING | FAILING | SKIPPED | NO_QG
coverage_pct: 0–100
bypass_audit_path: path/to/QUALITY_GATE_BYPASS_AUDIT.md
testing_level: unit | integration | e2e | none
skipped_gates: []
```

Current state: `NO_STATUS` for 40/55 repos.

### Quality Gates Missing Repos (12 repos, 10 agents)

Add `quality-gates.sh` using codex template:
`unified-api-contracts`, `unified-events-interface`, `unified-reference-data-interface`,
`alerting-service`, `unified-trade-execution-interface`, `features-calendar-service`,
`unified-position-interface`, `unified-trading-services`, `ml-training-service`,
`ml-inference-service`, `client-reporting-api`, `pnl-attribution-service`

### QG Baseline Run (4 agents, 30 repos)

Run quality gates on all 30 repos that already have `quality-gates.sh`.
Record `pass/fail + coverage % + bypass count` into manifest `ci_status` fields.
This is a **snapshot only** — do not fix failures yet (that is Phase 2/3 work).

### Cloud Build Audit (5 agents, 29 repos)

Verify all `cloudbuild.yaml` files follow `cloud-build-test-in-image.mdc`:

```
docker build → docker run quality-gates.sh --no-fix --quick → docker push (only if pass)
```

Fix any that run `pytest` or `ruff` outside the Docker image.

### AWS Parity (3 agents)

- `aws-compute-stubs-wire`: `aws_batch.py` + `aws_ec2.py` must match `cloud_run.py` interface
- `aws-secret-naming-parity`: mirror GCP Secret Manager naming in AWS SM
- `aws-cloudbuild-parity`: add `buildspec.aws.yaml` to all repos with `cloudbuild.yaml`

---

## DONE Criteria for Phase 1

All of the following must be true before Phase 2 starts:

- **A1 complete**: All 55 repos have `scripts/quickmerge.sh` + `.github/workflows/version-bump.yml`
- **A2 complete**: All 55 repos have commit-msg hook; all `pyproject.toml` versions are `0.x.x`
- **A3 complete**: dep-branch clone + Cloud Build feature trigger + GH Action version-bump live
- **B: visualizer extracted**: `execution-service` has no `visualizer-ui/` or `visualizer-api/`
- **B: UTD V3 split**: 4 separate repos (`deployment-service`, `deployment-api`, `deployment-ui`, `system-integration-tests`)
- **B: UI audit clean**: No embedded UI artifacts in any Python service repo
- **B: infra merged**: `ibkr-gateway-infra/` deleted from workspace root; Terraform in `deployment-service`
- **C: 3 cursor rules created**: `cloud-agnostic.mdc`, `dag-enforcement.mdc`, `ui-service-separation.mdc`
- **C: manifest schema extended**: `ci_status` fields present for all 55 repos
- **C: QG baseline recorded**: All 30 repos with QG have `ci_status` + `coverage_pct` in manifest
- **C: missing QGs added**: All 12 repos now have `quality-gates.sh`
- **C: Cloud Build audit**: All 29 `cloudbuild.yaml` run tests inside Docker image

---

## Cross-References

- **Phase 2** (library/service tier hardening): `phase2_library_tier_hardening.plan.md`
- **Phase 3** (service hardening + integration tests): `phase3_service_hardening_integration.plan.md`
- **Consolidated remaining work** (full task registry): `.cursor/plans/consolidated_remaining_work.plan.md`
- **Workspace manifest**: `unified-trading-pm/workspace-manifest.json`
- **Codex SSOT index**: `unified-trading-codex/00-SSOT-INDEX.md`
- **Runtime topology**: `unified-trading-deployment-v3/configs/runtime-topology.yaml`
- **New repo setup**: `unified-trading-pm/docs/new-repo-setup.md`
- **Integration testing layers**: `unified-trading-codex/06-coding-standards/integration-testing-layers.md`
- **UI service separation**: `unified-trading-codex/06-coding-standards/ui-service-separation.md`
