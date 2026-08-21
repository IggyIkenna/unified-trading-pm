---
doc_type: plan
title: dev-environment-automated-onboarding-2026-03-10
summary: Automated dev environment setup script that puts a developer into a fully working local dev environment in <15
  minutes with zero live API calls
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
type: infra
epic: epic-infra
superseded_by: cicd_code_rollout_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: local developer tooling — no cloud deployment required. BR N/A: internal tooling, no commercial KPI.'}
depends_on: [broken_symlinks_remediation_2026_03_09, api_keys_and_auth, defi_dev_testnet_data_rollout_2026_03_13]
todos:
- {id: phase-0-env-vars-doc, content: Document all required env vars and create .env.dev.template, status: todo, note: ''}
- {id: phase-1-setup-script, content: Create setup-dev-environment.sh with all 10 steps, status: todo, note: ''}
- {id: phase-2-dev-configs, content: Create dev runtime topology YAML and AWS/testnet docs, status: todo, note: ''}
- {id: phase-3-vcr-mode, content: Wire VCR_MODE toggle across all services, status: todo, note: ''}
- {id: phase-4-smoke-test, content: Create smoke-test-dev.py with 8 checks, status: todo, note: ''}
isProject: false
---

# Plan: Automated Dev Environment Setup & Onboarding

## Prerequisites (before running setup-dev-environment.sh)

**Every internal team member must have the following provisioned before running this script:**

- **Email (M365 Outlook)** — GitHub org invite and all internal comms go to this address. Without it, the developer
  cannot accept GitHub membership or receive Slack invites. See `user_management_platform_2026_03_13.md`.
- **Slack** — CI/CD alerts, trading alerts, and incident channels are all Slack-based. Slack invite is sent to the M365
  email.
- **GitHub org membership** — required to clone private repos. Invite is accepted via M365 email.

If any of these are missing, use `user-management-ui` (once built) or ask an admin to run the provisioning steps in
`user_management_platform_2026_03_13.md` first.

---

## Context

`workspace-bootstrap.sh` clones repos and sets up the workspace venv. Beyond that, a new developer (or new machine) must
manually: configure AWS testnet credentials, set environment variables across 60+ repos, configure VCR cassette mode,
set `CLOUD_MOCK_MODE`, and navigate broken symlinks. External data subscription auth (testnet keys for Binance, Deribit,
etc.) is undocumented. Goal: `bash setup-dev-environment.sh` from workspace root puts a developer into a fully working
local dev environment in <15 minutes, with zero live API calls, complete mock data, all quality gates passing.

---

## Phase 0: Document all required env vars

### P0.1 — Dev environment vars reference

File: `unified-trading-pm/docs/dev-environment-vars.md` (new)

Complete list:

```
# GCP
GCP_PROJECT_ID=central-element-323112
GOOGLE_APPLICATION_CREDENTIALS=/path/to/dev-sa-key.json

# Cloud mode
CLOUD_MOCK_MODE=true        # disables real GCS/PubSub calls
ENVIRONMENT=development
USE_SECRET_MANAGER=false    # use .env.dev overrides locally

# Runtime
RUNTIME_MODE=batch          # default for dev
CLOUD_PROVIDER=gcp          # or "local"
LOG_LEVEL=DEBUG

# AWS (testnet)
AWS_PROFILE=unified-trading-dev

# VCR
VCR_MODE=playback           # playback|record|disabled

# External API keys (all overridden by VCR cassettes in dev)
TARDIS_API_KEY=vcr_placeholder
DATABENTO_API_KEY=vcr_placeholder
ALCHEMY_API_KEY=vcr_placeholder
# ... (full list in .env.dev.template)
```

### P0.2 — .env.dev.template

File: `.env.dev.template` at workspace root Copy of all vars with annotations:

- `# REQUIRED — needs real value` vs `# DEFAULT — safe as-is` vs `# VCR — no real key needed in dev`

---

## Phase 1: setup-dev-environment.sh

File: `unified-trading-pm/scripts/workspace/setup-dev-environment.sh`

Steps the script executes:

```
1. check_prerequisites
   - python3.13, node 20+, docker, gcloud, aws, gh, uv
   - Print install instructions for any missing tool

2. run_workspace_bootstrap
   - If .venv-workspace absent: run workspace-bootstrap.sh --skip-fresh
   - source .venv-workspace/bin/activate

3. fix_broken_symlinks
   - Run fix-broken-symlinks.sh --all (from broken_symlinks_remediation plan)

4. setup_env_dev
   - If .env.dev absent: cp .env.dev.template .env.dev
   - Print: "Edit .env.dev to add your GCP dev SA key path"

5. configure_gcp_dev
   - gcloud config configurations create unified-trading-dev (idempotent)
   - gcloud config set project unified-trading-dev

6. configure_aws_testnet
   - If aws --profile unified-trading-dev sts get-caller-identity fails:
     Print: "Run: aws configure --profile unified-trading-dev"
     Print: "See unified-trading-pm/docs/aws-testnet-setup.md"

7. install_repo_dependencies
   - Parallel: for each repo with pyproject.toml: uv pip install -e . --quiet &

8. provision_dev_infra
   # seed-dev-project.sh RETIRED 2026-03-13 — use Terraform instead:
   - cd deployment-service/terraform/gcp && terraform apply -var="environment=dev" -var="project_id=central-element-323112"
   # For DeFi fork simulation (local):
   - anvil --fork-url https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY} --port 8545 &
   # See deployment-service/docs/dev-environment.md for full guide

9. run_smoke_test
   - python unified-trading-pm/scripts/dev/smoke-test-dev.py
   - Print PASS/FAIL per check

10. print_summary
    - "Dev environment ready."
    - "Source: source .venv-workspace/bin/activate"
    - List any warnings (e.g. AWS not configured)
```

---

## Phase 2: Dev-specific config files

### P2.1 — Dev runtime topology

File: `unified-trading-pm/configs/runtime-topology-dev.yaml`

Overrides for dev:

```yaml
defaults:
  transport_by_mode:
    batch:
      transport: "local" # local filesystem, no GCS
    live:
      transport: "in_memory" # in-process, no PubSub
  persistence:
    sink: "local"

service_clusters:
  all_services:
    deployment_target: "local"
```

### P2.2 — AWS testnet setup doc

File: `unified-trading-pm/docs/aws-testnet-setup.md`

Contents:

1. Create/use team shared AWS dev account (or personal account)
2. IAM permissions required (list exact policies per service role)
3. `aws configure --profile unified-trading-dev`
4. Verify: `aws --profile unified-trading-dev sts get-caller-identity`
5. ECR pull access for dev images (optional)
6. Secrets Manager dev namespace: `unified-trading/dev/` prefix for all dev secrets

### P2.3 — Testnet and sandbox API keys doc

File: `unified-trading-pm/docs/testnet-api-keys.md`

Per-venue testnet setup:

- **Binance testnet**: https://testnet.binance.vision — create account, generate API key
- **Deribit testnet**: https://test.deribit.com — create account, generate API key
- **Coinbase Advanced sandbox**: https://public.sandbox.exchange.coinbase.com — sandbox account
- **IBKR paper trading**: TWS paper account setup, IB Gateway paper port 7497
- **Betfair sandbox**: Betfair Developer Programme account + sandbox API key

In dev: all testnet keys should be stored in `.env.dev` (not Secret Manager) so VCR recording works. In staging: testnet
keys stored in Secret Manager under `unified-trading/staging/` namespace.

---

## Phase 3: VCR cassette dev mode

### P3.1 — Global VCR mode toggle

All services read `VCR_MODE=record|playback|disabled` env var.

```
dev:      VCR_MODE=playback  (use committed cassettes — no live calls)
CI:       VCR_MODE=playback  (same cassettes)
staging:  VCR_MODE=disabled  (real APIs, testnet keys)
prod:     VCR_MODE=disabled  (real APIs, production keys)
```

### P3.2 — Cassette location

After `api_keys_and_auth.md` Phase 1–4 records cassettes, commit them to:
`unified-trading-pm/scripts/dev/vcr_cassettes/{venue}/{endpoint}.yaml`

No secrets in cassette files — only response bodies, stripped of auth headers.

---

## Phase 4: Dev smoke test

### P4.1 — smoke-test-dev.py

File: `unified-trading-pm/scripts/dev/smoke-test-dev.py`

Checks (each prints PASS/FAIL):

1. Python 3.13 active from `.venv-workspace/bin/python`
2. All T0–T3 libraries importable (UTL, UCI, UEI, UAC, UIC, UMI)
3. `CLOUD_MOCK_MODE=true` → mock GCS read/write completes without real credentials
4. `VCR_MODE=playback` → top 3 venue cassettes present and parseable
5. Dev GCP project configured (project = `unified-trading-dev`)
6. `setup_events()` from UEI works without real Pub/Sub
7. `ruff check unified-trading-library/` exits 0
8. `run_timeout 120 basedpyright unified-trading-library/` exits 0

---

## Verification Gates

- [ ] New developer: clone workspace → `bash setup-dev-environment.sh` → all 9 steps pass
- [ ] `smoke-test-dev.py` exits 0 with all 8 checks PASS
- [ ] Zero live external API calls during setup (VCR_MODE=playback throughout)
- [ ] All services importable with only `.env.dev` (no real SM credentials)
- [ ] Script is idempotent: running twice doesn't break anything

## Files Created / Modified

- `unified-trading-pm/scripts/workspace/setup-dev-environment.sh` (new)
- `.env.dev.template` (workspace root, new)
- `unified-trading-pm/configs/runtime-topology-dev.yaml` (new)
- `unified-trading-pm/docs/dev-environment-vars.md` (new)
- `unified-trading-pm/docs/aws-testnet-setup.md` (new)
- `unified-trading-pm/docs/testnet-api-keys.md` (new)
- `unified-trading-pm/scripts/dev/smoke-test-dev.py` (new)

## Dependencies

- `broken_symlinks_remediation_2026_03_09.md` (fix-broken-symlinks.sh must exist)
- `api_keys_and_auth.md` (VCR cassettes Phase 1–4 needed for full playback)
- `mock_data_dev_project_seeding_2026_03_10.md` (seed-dev-project.sh called in step 8)
