---
name: staging-deployment-mock-gate-2026-03-11
overview: |
  Add a per-repo deployment smoke test as the third required gate on the staging branch
  (alongside quality-gates and staging-lock-check). Each service/API repo builds its own
  Docker container with CLOUD_MOCK_MODE=true + GCP emulators, runs real HTTP calls against
  the live container, and posts the result as the "Deployment Smoke / deployment-smoke" status
  check. Libraries (no HTTP server) auto-pass. This gives a fast (<10 min) container-level
  smoke test on every staging PR before SIT runs the full cross-service deployment-tests suite.
type: infra
epic: epic-infra
status: active

completion_gates:
  code: C5
  deployment: D2
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
    readiness_note: |
      Templates: deployment-smoke.yml, docker-compose.single.yml (service/api/library variants).
      Propagation script update. Staging ruleset update (add 3rd check). Docker profile docs.
  - repo: system-integration-tests
    code: C0
    deployment: none
    business: none
    readiness_note: |
      Phase 2 todos (phase2-service-mock-replay, phase2-error-events) in production_mock_e2e_plan
      generate the deployment_test-marked tests that this gate runs. Phase 2 completion = D2 for SIT.
  - repo: execution-service
    code: C0
    deployment: none
    business: none
    readiness_note: "Representative T4 service. deployment-smoke.yml + deployment_test markers."
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
    readiness_note: "Representative T4 service."
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
    readiness_note: "Representative T5 API."

depends_on:
  - production_mock_e2e_plan_d90c8f20

todos:
  # ─── PHASE 1: SINGLE-SERVICE DOCKER COMPOSE TEMPLATE ───

  - id: ds1-docker-single-service-template
    content: |
      Create `unified-trading-pm/docker/docker-compose.single.yml` — a parameterised single-service
      stack that deployment-smoke.yml brings up for each repo.

      Design: uses Docker Compose profiles so each service only starts itself + its required emulators.
      The service image is always built from local source (build: context: ../../${SERVICE_NAME}).

      Service types and what they need:
        service (T3/T4): PubSub emulator, GCS emulator, BigQuery emulator (optional)
        api (T5): GCS emulator only (for health endpoint state); no PubSub
        library (T0-T2): no Docker needed — auto-pass (workflow exits 0 immediately)
        ui (T6): no Docker needed — auto-pass

      Template structure:
      ```yaml
      version: "3.9"
      x-mock-env: &mock-env
        CLOUD_PROVIDER: local
        CLOUD_MOCK_MODE: "true"
        PUBSUB_EMULATOR_HOST: pubsub-emulator:8085
        STORAGE_EMULATOR_HOST: http://gcs-emulator:4443
        BIGQUERY_EMULATOR_HOST: bigquery-emulator:9050
        LOG_LEVEL: INFO
      services:
        pubsub-emulator:
          image: gcr.io/google.com/cloudsdktool/google-cloud-cli:latest
          command: gcloud beta emulators pubsub start --host-port=0.0.0.0:8085 --project=mock-project
          ports: ["8085:8085"]
          healthcheck: {test: ["CMD","curl","-f","http://localhost:8085"], interval: 5s, retries: 10}
          profiles: ["service"]
        gcs-emulator:
          image: fsouza/fake-gcs-server:latest
          ports: ["4443:4443"]
          command: -scheme http -port 4443
          healthcheck: {test: ["CMD","curl","-f","http://localhost:4443/storage/v1/b"], interval: 5s, retries: 10}
          profiles: ["service", "api"]
        target-service:
          build:
            context: ../../${SERVICE_REPO:-execution-service}
            dockerfile: Dockerfile
          environment:
            <<: *mock-env
            SERVICE_PORT: "8000"
          ports: ["8000:8000"]
          healthcheck: {test: ["CMD","curl","-f","http://localhost:8000/health"], interval: 5s, retries: 20}
          depends_on:
            pubsub-emulator: {condition: service_healthy}
            gcs-emulator: {condition: service_healthy}
          profiles: ["service", "api"]
      ```

      Each repo's `Dockerfile` must already exist (tracked in production_mock_e2e_plan h10-1 — docker-compose.mock.yml
      already builds each service from source using build: context: ../../{service}).
      CRITICAL: SERVICE_REPO env var is set by deployment-smoke.yml to `${{ github.event.repository.name }}`.
    status: done
    note: "Blocked only by availability of Dockerfiles. Most services already have them from docker-compose.mock.yml."

  - id: ds2-deployment-smoke-gha-template
    content: |
      Create `unified-trading-pm/scripts/propagation/templates/deployment-smoke.yml`:

      TRIGGER: pull_request: branches: [staging], types: [opened, reopened, synchronize]

      LOGIC:
      1. Detect repo type from workspace-manifest.json (fetch via API, same as staging-lock-check.yml).
         Read: repositories[{repo}].repo_type (values: library, service, api, ui, infra)
         If type is library | ui | infra: skip — post success outcome immediately (exit 0, no Docker needed).
      2. Set COMPOSE_PROFILE based on type: service → "service", api → "api"
      3. Copy docker-compose.single.yml from PM repo (checkout or fetch via API)
      4. Build + start the stack: docker compose -f docker-compose.single.yml --profile $COMPOSE_PROFILE up -d --build
         Timeout: 5 minutes. On timeout: fail with "container failed to start".
      5. Wait for service health: retry curl http://localhost:8000/health every 10s, timeout 3 min.
      6. Run deployment tests:
         pytest tests/ -m deployment_test --timeout=120 -q --tb=short
         OR (if no deployment_test markers exist yet): pytest tests/smoke/ -q --tb=short
         Use -m deployment_test when markers exist, fall back to smoke/ until phase2 adds them.
      7. Tear down: docker compose -f docker-compose.single.yml --profile $COMPOSE_PROFILE down -v
      8. Exit 0 on pass, exit 1 on failure.

      Required status check name: "Deployment Smoke / deployment-smoke"
      (workflow name: "Deployment Smoke", job name: "deployment-smoke")

      PERMISSIONS: contents: read

      key env vars:
        GH_TOKEN: ${{ secrets.GH_PAT }}      (for manifest fetch)
        SERVICE_REPO: ${{ github.event.repository.name }}  (passed to docker-compose.single.yml)

      IMPORTANT: libraries/ui repos emit a soft-pass message: "Library repo — no deployment smoke needed. ✅"
      and exit 0. This ensures the status check always resolves (never stays pending).
    status: done
    blocked_by: ds1-docker-single-service-template

  # ─── PHASE 2: PER-REPO DEPLOYMENT TEST MARKERS ───

  - id: ds3-deployment-test-marker-protocol
    content: |
      Define the @pytest.mark.deployment_test protocol and add it to existing tests.
      This is the interface between the per-repo deployment-smoke gate and the existing test suites.

      Protocol:
      - @pytest.mark.deployment_test: test requires a running service container (real HTTP calls to localhost)
      - NOT @pytest.mark.deployment_test: test uses unit mocks only (runs without Docker)

      Per-repo guidance (first batch — T4 services, T5 APIs):
        execution-service: tests/integration/test_order_api.py, tests/integration/test_health.py
        strategy-service: tests/integration/test_strategy_api.py, tests/integration/test_health.py
        risk-and-exposure-service: tests/integration/test_risk_api.py
        deployment-api: tests/smoke/test_api_smoke.py → deployment_test
        alerting-service: tests/integration/test_alert_webhooks.py

      Add to each repo's pyproject.toml:
        [tool.pytest.ini_options]
        markers = [
          "deployment_test: requires running service container (real HTTP calls via docker-compose.single.yml)",
        ]

      Rollout order: T5 APIs first (simplest), then T4 services, then T3 services.
      Libraries and UIs: no markers needed (deployment-smoke.yml auto-passes for these).

      This todo is satisfied when: ≥1 deployment_test-marked test exists in each T4+T5 repo.
      Full coverage (all integration tests marked) tracked in production_mock_e2e_plan phase2-service-mock-replay.
    status: done

  # ─── PHASE 3: ROLLOUT ───

  - id: ds4-rollout-template-to-repos
    content: |
      Roll out deployment-smoke.yml to all 63 repos via the propagation script.

      Rollout includes:
      1. Copy deployment-smoke.yml to .github/workflows/deployment-smoke.yml in each repo
      2. Add the pyproject.toml marker declaration (append to [tool.pytest.ini_options].markers)
         for Python repos; skip for UI repos
      3. Commit: "chore(ci): add deployment-smoke workflow for staging mock deployment gate"

      Exclude: unified-trading-pm, unified-trading-codex (infra, auto-pass in the workflow anyway).

      Use the same rollout pattern as staging-lock-check rollout (PUT via GitHub API).
    status: todo
    blocked_by: ds2-deployment-smoke-gha-template

  - id: ds5-add-third-staging-check
    content: |
      Add "Deployment Smoke / deployment-smoke" as a third required check to the
      require-staging-lock-check ruleset on all repos.

      Current staging ruleset has 2 required checks:
        - quality-gates
        - Staging Lock Check / check-staging-lock

      After this todo: 3 required checks:
        - quality-gates
        - Staging Lock Check / check-staging-lock
        - Deployment Smoke / deployment-smoke

      Implementation:
        gh api repos/IggyIkenna/{repo}/rulesets/{id} -X PUT
        with updated required_status_checks array including all 3 contexts.

      For library/UI repos: the workflow auto-passes (exit 0 immediately), so requiring the check
      does NOT block library PRs — it just always passes.

      Do NOT add this check until ds4 rollout is complete and at least 5 repos have been verified
      to pass the deployment-smoke check successfully (to avoid accidentally blocking all staging PRs).
    status: todo
    blocked_by: ds4-rollout-template-to-repos
    note: |
      SAFETY GATE: Only apply the branch protection addition after verifying smoke tests pass.
      Intermediate state: workflow runs informatively (not a required check) until verified.

  # ─── PHASE 4: PRODUCTION_MOCK_E2E ALIGNMENT ───

  - id: ds6-production-mock-e2e-plan-sync
    content: |
      Update production_mock_e2e_plan_d90c8f20.md:
      Mark phase2-service-mock-replay and phase2-error-events as the implementation layer for
      deployment_test markers. These todos now have a concrete CI target: once markers are added
      (ds3), the deployment-smoke gate in GHA picks them up automatically.

      Add a note to both phase2 todos:
        "CI gate: deployment-smoke.yml on staging PRs runs these tests automatically.
         See staging_deployment_mock_gate_2026_03_11.md for the gate implementation."

      This clarifies the relationship: production_mock_e2e = test CONTENT; this plan = CI WIRING.
    status: done

isProject: false
---

# Staging Deployment Mock Gate

## Problem

The current staging branch requires:

1. `quality-gates` — unit tests, lint, typecheck (no running service)
2. `staging-lock-check` — SIT not running

There is **no per-repo test that verifies "does this service's container actually start and serve correct API responses
with mocked infrastructure?"** This class of bug currently only surfaces during SIT (Layer 3b/3c deployment-tests),
which runs the full cross-service docker-compose stack AFTER PRs already merged to staging. Boot failures, missing env
vars, wrong port bindings, and basic API contract regressions are caught too late.

## Target State

Each staging PR for a service/API repo must pass a **deployment smoke check** before auto-merging:

```
feat/my-change PR → staging
  [1] quality-gates              ← unit/lint/typecheck (no container)
  [2] staging-lock-check         ← SIT not running
  [3] Deployment Smoke           ← THIS PLAN
        build container from PR source
        start with CLOUD_MOCK_MODE=true + GCP emulators
        hit /health → must return 200
        run pytest -m deployment_test → must pass
        ↓ passes → auto-merge to staging
```

Libraries and UI repos: the check fires but exits 0 immediately (no container needed).

## Architecture

```
Each service/API repo:
  deployment-smoke.yml  (per-repo, in .github/workflows/)
    ↓
  fetches workspace-manifest.json from PM to detect repo_type
    ↓ (if library/ui/infra)           ↓ (if service/api)
  ✅ auto-pass                    docker compose up (single-service profile)
                                       ↑
                              docker-compose.single.yml (PM template)
                              - target-service (built from current PR source)
                              - pubsub-emulator (if service type)
                              - gcs-emulator (if service or api type)
                                       ↓
                              pytest -m deployment_test (real HTTP to localhost)
                                       ↓
                              docker compose down -v
                                       ↓
                              ✅ pass / ❌ fail
```

## Relationship to Existing Plans

| Plan                                                  | Relationship                                                                                                                     |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `production_mock_e2e_plan_d90c8f20`                   | Phase 2 generates the `deployment_test`-marked tests. This plan provides the CI wiring (the gate) that runs them on staging PRs. |
| `cicd_versioning_cloud_build_2026_03_11` (archived)   | Defined the SIT code/deployment split. This plan adds the per-repo equivalent BEFORE SIT.                                        |
| `staging_deployment_mock_gate_2026_03_11` (this plan) | The CI gate.                                                                                                                     |

## Deployment Smoke vs SIT Deployment Tests

| Dimension      | Deployment Smoke (this plan)   | SIT Deployment Tests              |
| -------------- | ------------------------------ | --------------------------------- |
| Trigger        | On every staging PR (per-repo) | After all PRs merge to staging    |
| Scope          | Single repo + its emulators    | Full 65-repo docker-compose stack |
| Speed          | < 10 min                       | 30–60 min                         |
| Purpose        | Boot + API contract check      | Cross-service integration         |
| Failure impact | Blocks that repo's PR          | Locks staging, blocks all         |

## Key Files

| File                                                 | Repo         | Purpose                      |
| ---------------------------------------------------- | ------------ | ---------------------------- |
| `scripts/propagation/templates/deployment-smoke.yml` | pm           | GHA template                 |
| `docker/docker-compose.single.yml`                   | pm           | Single-service compose stack |
| `.github/workflows/deployment-smoke.yml`             | all 63 repos | Rolled out from template     |
| `production_mock_e2e_plan_d90c8f20.md`          | pm           | Test content (phase 2)       |
