---

name: gha-ci-tools-centralization overview: | Centralizes GHA and Cloud Build CI tool installation across all ~65 repos
into versioned, cached composite actions (GHA) and a shared ci-tools builder image (Cloud Build). Currently every repo
installs ripgrep, uv, jq, and Python dev tools inline — no version pinning, no caching, no single source of truth. This
plan: 1. Creates 3 GHA composite actions in unified-trading-pm (python-tools, ui-tools, agent-tools) 2. Creates a Cloud
Build ci-tools Docker image in unified-trading-pm's Artifact Registry namespace 3. Rolls out adoption tier-by-tier: PM →
T0 libs → T1-T2 interfaces → T3-T4 services → T5 APIs → T6 UIs → infra AWS CodeBuild is not used in this workspace (no
buildspec files exist) — scope is GHA + GCP Cloud Build only. type: infra epic: epic-infrastructure status: archived

tool_versions: ripgrep: "14.1.1" shellcheck: "v0.10.0" python: "3.13.9" node: "20" uv: "latest" # pinned via
requirements in action

completion_gates: code: C5 deployment: none business: none

phases:

- id: P0 name: PM — create composite actions + ci-tools image repos: [unified-trading-pm] deliverables:
  - .github/actions/setup-python-tools/action.yml
  - .github/actions/setup-ui-tools/action.yml
  - .github/actions/setup-agent-tools/action.yml
  - docker/ci-tools/Dockerfile
  - .github/workflows/build-ci-tools-image.yml notes: | Composite actions are usable by other repos immediately after
    merge to main. ci-tools image must be built+pushed before Cloud Build migration steps run. Update PM's own
    quality-gates.yml to use setup-python-tools composite action.

- id: P1 name: T0 Libraries repos:
  - execution-algo-library
  - matching-engine-library
  - unified-feature-calculator-library
  - unified-trading-library notes: | Lowest dependency tier — safest to migrate first. GHA: replace inline installs with
    uses: IggyIkenna/unified-trading-pm/.github/actions/setup-python-tools@main Cloud Build: replace sudo apt-get
    install ripgrep with ci-tools image step.

- id: P2 name: T1-T2 Interfaces + Contracts repos:
  - unified-events-interface
  - unified-cloud-interface
  - unified-config-interface
  - unified-market-interface
  - unified-trade-execution-interface
  - unified-domain-client
  - unified-reference-data-interface
  - unified-position-interface
  - unified-ml-interface
  - unified-defi-execution-interface
  - unified-sports-execution-interface
  - unified-api-contracts
  - unified-internal-contracts notes: | Interface repos often install sibling deps — composite action handles only tool
    setup, dep install steps remain per-repo.

- id: P3 name: T3-T4 Services repos:
  - instruments-service
  - market-tick-data-service
  - market-data-processing-service
  - features-delta-one-service
  - features-volatility-service
  - features-calendar-service
  - features-onchain-service
  - features-sports-service
  - features-cross-instrument-service
  - features-multi-timeframe-service
  - features-commodity-service
  - strategy-validation-service
  - execution-service
  - strategy-service
  - risk-and-exposure-service
  - alerting-service
  - pnl-attribution-service
  - position-balance-monitor-service
  - trading-agent-service
  - ml-training-service
  - ml-inference-service
  - batch-live-reconciliation-service
  - elysium-defi-system
  - deployment-service notes: | Service repos may also have agent-audit.yml — use setup-agent-tools for those.
    GCP-authed services (execution, strategy, ml-\*) keep their GCP auth step; only tool install steps are replaced.

- id: P4 name: T5 API Services repos:
  - market-data-api
  - execution-results-api
  - batch-audit-api
  - ml-training-api
  - ml-inference-api
  - client-reporting-api
  - deployment-api
  - trading-analytics-api

- id: P5 name: T6 UI Repos repos:
  - deployment-ui
  - execution-analytics-ui
  - batch-audit-ui
  - trading-analytics-ui
  - strategy-ui
  - ml-training-ui
  - client-reporting-ui
  - live-health-monitor-ui
  - logs-dashboard-ui
  - onboarding-ui
  - settlement-ui
  - unified-admin-ui
  - unified-trading-ui-auth
  - unified-trading-ui-kit notes: | UI repos use setup-ui-tools (Node only — no ripgrep needed). Cloud Build UI pattern
    runs QG in node:20-alpine; no change needed there unless we add an optional rg install to setup-ui-tools.

- id: P6 name: Infrastructure + Special Repos repos:
  - ibkr-gateway-infra
  - system-integration-tests
  - unified-trading-codex notes: | ibkr-gateway-infra needs shellcheck in addition to rg — setup-python-tools includes
    shellcheck install; or use infra variant if added later.

repo_gates:

- repo: unified-trading-pm code: C4 deployment: none business: none readiness_note: "P0 — owns composite actions and
  ci-tools image. Must land first."

- repo: execution-algo-library code: C4 deployment: none business: none readiness_note: "P1 T0 library."

- repo: matching-engine-library code: C4 deployment: none business: none readiness_note: "P1 T0 library."

- repo: unified-feature-calculator-library code: C4 deployment: none business: none readiness_note: "P1 T0 library."

- repo: unified-trading-library code: C4 deployment: none business: none readiness_note: "P1 T0 library. Base image for
  most Python services."

- repo: unified-events-interface code: C4 deployment: none business: none readiness_note: "P2 T1 interface."

- repo: unified-cloud-interface code: C4 deployment: none business: none readiness_note: "P2 T1 interface."

- repo: unified-config-interface code: C4 deployment: none business: none readiness_note: "P2 T1 interface."

- repo: unified-market-interface code: C4 deployment: none business: none readiness_note: "P2 T2 interface."

- repo: unified-trade-execution-interface code: C4 deployment: none business: none readiness_note: "P2 T2 interface."

- repo: unified-domain-client code: C4 deployment: none business: none readiness_note: "P2 T2 interface."

- repo: unified-reference-data-interface code: C4 deployment: none business: none readiness_note: "P2 T2 interface."

- repo: unified-position-interface code: C4 deployment: none business: none readiness_note: "P2 T2 interface."

- repo: unified-ml-interface code: C4 deployment: none business: none readiness_note: "P2 T2 interface."

- repo: unified-defi-execution-interface code: C4 deployment: none business: none readiness_note: "P2 T2 interface."

- repo: unified-sports-execution-interface code: C4 deployment: none business: none readiness_note: "P2 T2 interface."

- repo: unified-api-contracts code: C4 deployment: none business: none readiness_note: "P2 T2 contracts."

- repo: unified-internal-contracts code: C4 deployment: none business: none readiness_note: "P2 T2 contracts."

- repo: instruments-service code: C4 deployment: none business: none readiness_note: "P3 T3 service."

- repo: market-tick-data-service code: C4 deployment: none business: none readiness_note: "P3 T3 service."

- repo: market-data-processing-service code: C4 deployment: none business: none readiness_note: "P3 T3 service."

- repo: features-delta-one-service code: C4 deployment: none business: none readiness_note: "P3 T3 feature service."

- repo: features-volatility-service code: C4 deployment: none business: none readiness_note: "P3 T3 feature service."

- repo: features-calendar-service code: C4 deployment: none business: none readiness_note: "P3 T3 feature service."

- repo: features-onchain-service code: C4 deployment: none business: none readiness_note: "P3 T3 feature service."

- repo: features-sports-service code: C4 deployment: none business: none readiness_note: "P3 T3 feature service."

- repo: features-cross-instrument-service code: C4 deployment: none business: none readiness_note: "P3 T3 feature
  service."

- repo: features-multi-timeframe-service code: C4 deployment: none business: none readiness_note: "P3 T3 feature
  service."

- repo: features-commodity-service code: C4 deployment: none business: none readiness_note: "P3 T3 feature service."

- repo: strategy-validation-service code: C4 deployment: none business: none readiness_note: "P3 T3 service."

- repo: execution-service code: C4 deployment: none business: none readiness_note: "P3 T4 core service. Has GCP auth
  step — keep it, only replace tool installs."

- repo: strategy-service code: C4 deployment: none business: none readiness_note: "P3 T4 core service."

- repo: risk-and-exposure-service code: C4 deployment: none business: none readiness_note: "P3 T4 core service."

- repo: alerting-service code: C4 deployment: none business: none readiness_note: "P3 T4 core service."

- repo: pnl-attribution-service code: C4 deployment: none business: none readiness_note: "P3 T4 service."

- repo: position-balance-monitor-service code: C4 deployment: none business: none readiness_note: "P3 T4 service."

- repo: trading-agent-service code: C4 deployment: none business: none readiness_note: "P3 T4 service. Has
  agent-audit.yml — use setup-agent-tools for that workflow."

- repo: ml-training-service code: C4 deployment: none business: none readiness_note: "P3 T4 ML service."

- repo: ml-inference-service code: C4 deployment: none business: none readiness_note: "P3 T4 ML service."

- repo: batch-live-reconciliation-service code: C4 deployment: none business: none readiness_note: "P3 T4 batch
  service."

- repo: elysium-defi-system code: C4 deployment: none business: none readiness_note: "P3 T4 DeFi service."

- repo: deployment-service code: C4 deployment: none business: none readiness_note: "P3 T4 infra service."

- repo: market-data-api code: C4 deployment: none business: none readiness_note: "P4 T5 API."

- repo: execution-results-api code: C4 deployment: none business: none readiness_note: "P4 T5 API."

- repo: batch-audit-api code: C4 deployment: none business: none readiness_note: "P4 T5 API."

- repo: ml-training-api code: C4 deployment: none business: none readiness_note: "P4 T5 API."

- repo: ml-inference-api code: C4 deployment: none business: none readiness_note: "P4 T5 API."

- repo: client-reporting-api code: C4 deployment: none business: none readiness_note: "P4 T5 API."

- repo: deployment-api code: C4 deployment: none business: none readiness_note: "P4 T5 API."

- repo: trading-analytics-api code: C4 deployment: none business: none readiness_note: "P4 T5 API."

- repo: deployment-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI. Uses setup-ui-tools."

- repo: execution-analytics-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: batch-audit-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: trading-analytics-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: strategy-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: ml-training-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: client-reporting-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: live-health-monitor-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: logs-dashboard-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: onboarding-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: settlement-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: unified-admin-ui code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: unified-trading-ui-auth code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: unified-trading-ui-kit code: C4 deployment: none business: none readiness_note: "P5 T6 UI."

- repo: ibkr-gateway-infra code: C4 deployment: none business: none readiness_note: "P6 infra — also needs shellcheck."

- repo: system-integration-tests code: C4 deployment: none business: none readiness_note: "P6 special repo."

- repo: unified-trading-codex code: C4 deployment: none business: none readiness_note: "P6 special repo."

migration_pattern: gha_python: | # BEFORE (inline in each workflow): - name: Install UV run: pip install uv - name:
Install ripgrep (required for codex checks) run: sudo apt-get update && sudo apt-get install -y ripgrep

    # AFTER (composite action):
    - name: Setup Python CI tools
      uses: IggyIkenna/unified-trading-pm/.github/actions/setup-python-tools@main
      with:
        python-version: "3.13.9"

gha_ui: | # BEFORE: - name: Setup Node.js uses: actions/setup-node@v4 with: node-version: "20" cache: "npm"

    # AFTER:
    - name: Setup UI CI tools
      uses: IggyIkenna/unified-trading-pm/.github/actions/setup-ui-tools@main

gha_agent: | # BEFORE (inline in agent-audit.yml): - run: sudo apt-get install -y -qq ripgrep jq - run: pip install uv -
run: npm install -g @anthropic-ai/claude-code

    # AFTER:
    - name: Setup agent CI tools
      uses: IggyIkenna/unified-trading-pm/.github/actions/setup-agent-tools@main

cloud_build_python: | # BEFORE (inline step in cloudbuild.yaml): - name: 'ubuntu' entrypoint: bash args: ['-c', 'apt-get
update && apt-get install -y ripgrep && bash scripts/quality-gates.sh --no-fix']

    # AFTER (dedicated step using ci-tools builder image):
    - name: 'asia-northeast1-docker.pkg.dev/$PROJECT_ID/unified-trading-pm/ci-tools:latest'
      entrypoint: bash
      id: quality-gates
      args: ['-c', 'bash scripts/quality-gates.sh --no-fix']

aws_codebuild: status: not-applicable reason: | No buildspec.yml files exist in this workspace. All CI runs on GHA + GCP
Cloud Build. If AWS CodeBuild is added in future, create setup-python-tools equivalent for buildspec and add it to this
plan.
