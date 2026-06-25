---
scope: [engineer, admin]
status: BACKEND-ORCHESTRATION-SSOT (frontend sections trimmed 2026-05-12 per UI-1/UI-14)
last_reviewed: 2026-06-25
---

# Local Development Guide — backend orchestration SSOT

> **Decision table — which startup script when** (codified 2026-05-12 per UI-1/UI-14 audit):
>
> | Use case                                                    | Script                                                                         | Reference                                                                                 |
> | ----------------------------------------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
> | Consolidated portal / UI work (default)                     | `bash unified-trading-system-ui/scripts/dev-tiers.sh --tier {static\|0\|1\|2}` | [`runtime-tiers-and-deployment.md`](../05-infrastructure/runtime-tiers-and-deployment.md) |
> | Firebase emulator suite (auth/admin work)                   | covered by `dev-tiers.sh --tier 0` (auto-seeds 23 demo personas)               | [`firebase-local.md`](../14-customer-journeys/authentication/firebase-local.md)           |
> | deployment-api (port 8004) + deployment-ui (port 5183) only | `bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh`              | `cursor-configs/CLAUDE.md` § "Deployment-stack restart (SSOT)"                            |
> | Backend service ad-hoc spin-up (8004-8016 range)            | `bash unified-trading-pm/scripts/dev/dev-start.sh` (this doc)                  | —                                                                                         |
>
> This doc covers the **backend orchestration** half (`dev-start.sh` / `dev-stop.sh` / `dev-status.sh`). The frontend /
> consolidated-portal half was trimmed 2026-05-12 (UI-1 + UI-3 + UI-5 + UI-14) — for portal startup, mode-axis collapse
> to `runtime_profile` v7, and the live UI port mapping see
> [`runtime-tiers-and-deployment.md`](../05-infrastructure/runtime-tiers-and-deployment.md) and
> `unified-trading-pm/scripts/dev/ui-api-mapping.json` (the machine-readable port SSOT).

---

**SSOT for:** Starting, stopping, and verifying the Unified Trading System locally. Port assignments, mode axes,
mock/real semantics, hot reload, zombie process prevention.

**Scripts:** `unified-trading-pm/scripts/dev/dev-start.sh`, `dev-stop.sh`, `dev-status.sh`

**Port mapping data:** `unified-trading-pm/scripts/dev/ui-api-mapping.json`

**Cross-repo operational modes:** For the canonical env-axis matrix (including `DATA_MODE`, `TESTNET_MODE`, migration
from `CLOUD_MOCK_MODE`, and Layer 3 SIT expectations), see
[operational-modes-matrix.md](../09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md). This guide
focuses on `dev-start.sh` presets and UI-specific toggles.

---

## Mode System — `dev-start.sh` backend axes

> **2026-05-12 UI-3 reconciliation**: the original 5-axis matrix (`VITE_MOCK_API` / `VITE_SKIP_AUTH` / `CLOUD_MOCK_MODE`
> / `DISABLE_AUTH` / `MOCK_STATE_MODE`) was split by the consolidated-portal migration. `VITE_*` axes are obsolete
> (Next.js uses `NEXT_PUBLIC_MOCK_API` / `NEXT_PUBLIC_USE_FIREBASE_EMULATOR` — see `unified-trading-system-ui` repo).
> The 5 env vars also collapsed into the single `runtime_profile` axis for deployment-api per
> [`runtime-tiers-and-deployment.md`](../05-infrastructure/runtime-tiers-and-deployment.md) § "Runtime Profiles (v7)".
> The backend axes documented below remain accurate for ad-hoc service spin-up via `dev-start.sh` — they are NOT the
> SSOT for portal startup.

The `dev-start.sh` backend stack has 3 independent mode axes (the UI axes above are deprecated):

| Axis           | Env Var           | Mock value                                               | Real value                                       | Controls                            |
| -------------- | ----------------- | -------------------------------------------------------- | ------------------------------------------------ | ----------------------------------- |
| **API data**   | `CLOUD_MOCK_MODE` | `true` (mock_data.py)                                    | `false` (cloud storage)                          | Sample data vs real cloud reads     |
| **API auth**   | `DISABLE_AUTH`    | `true` (no tokens)                                       | unset (tokens required)                          | Token validation                    |
| **Mock state** | `MOCK_STATE_MODE` | `interactive` (mutations persist in `.local-dev-cache/`) | `deterministic` (pure seed data, no persistence) | Stateful vs stateless mock behavior |

### Preset Modes

```bash
# Fully mocked, interactive state (default) — no credentials needed
# Mutations persist in .local-dev-cache/ across API restarts
bash scripts/dev/dev-start.sh --all --mode mock

# Fully mocked, deterministic state — CI/test, no persistence
# Every run starts from pure seed data, no .local-dev-cache/ writes
bash scripts/dev/dev-start.sh --all --mode ci

# UI mocked, API real — test API against real cloud data
bash scripts/dev/dev-start.sh --all --mode api-real

# Everything real — staging-like, needs credentials + OAuth client ID
bash scripts/dev/dev-start.sh --all --mode real
```

### Checking Current Mode

```bash
bash scripts/dev/dev-status.sh
# Shows all 5 axes with color coding (yellow = mocked, green = real, cyan = deterministic)
```

---

## Starting the Stack

All commands run from the workspace root.

```bash
# Full stack in mock mode (default — no credentials needed)
bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock

# Specific stack (e.g. deployment UI + API)
bash unified-trading-pm/scripts/dev/dev-start.sh --stack deployment --mode mock

# Frontend only (backends already running or not needed)
bash unified-trading-pm/scripts/dev/dev-start.sh --all --frontend-only

# Backend only
bash unified-trading-pm/scripts/dev/dev-start.sh --all --backend-only --mode mock

# Real mode (requires cloud credentials)
bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode real

# Single UI or API
bash unified-trading-pm/scripts/dev/dev-start.sh --ui deployment-ui
bash unified-trading-pm/scripts/dev/dev-start.sh --api deployment-api --mode real

# List all available stacks and ports
bash unified-trading-pm/scripts/dev/dev-start.sh --list
```

---

## Port Registry

> **2026-05-12 UI-1 reconciliation**: the per-UI 5173-5183 table that lived here listed 11 split-Vite UIs
> (`onboarding-ui` / `execution-analytics-ui` / `strategy-ui` / `settlement-ui` / `live-health-monitor-ui` /
> `logs-dashboard-ui` / `ml-training-ui` / `trading-analytics-ui` / `batch-audit-ui` / `client-reporting-ui` /
> `deployment-ui`). All but `deployment-ui` are archived (consolidated into `unified-trading-system-ui` per
> `codex/DEPRECATED_UIS_NOTICE.md` + `05-infrastructure/ui-functionality-requirements.md`). For the live UI port mapping
> see `unified-trading-pm/scripts/dev/ui-api-mapping.json` (machine-readable SSOT) +
> [`runtime-tiers-and-deployment.md`](../05-infrastructure/runtime-tiers-and-deployment.md) (consolidated portal ports:
> `unified-trading-system-ui` Next.js dev `:3000`, real-API server `:3100`; `deployment-ui` `:5183`).

### API Ports (8004-8016)

| Port | API Repo              | Stack               |
| ---- | --------------------- | ------------------- |
| 8004 | deployment-api        | deployment          |
| 8005 | config-api            | onboarding          |
| 8006 | execution-results-api | execution-analytics |
| 8007 | (reserved)            | strategy            |
| 8008 | (reserved)            | settlement          |
| 8009 | (reserved)            | live-health-monitor |
| 8010 | (reserved)            | logs-dashboard      |
| 8011 | ml-training-api       | ml-training         |
| 8012 | trading-analytics-api | trading-analytics   |
| 8013 | batch-audit-api       | batch-audit         |
| 8014 | client-reporting-api  | client-reporting    |
| 8015 | ml-inference-api      | ml-inference        |
| 8026 | agent-orchestrator    | agent-orchestrator  |

**Machine-readable SSOT:** `unified-trading-pm/scripts/dev/ui-api-mapping.json`

**strictPort:** All UIs use `strictPort: true` in Vite config. If a port is already in use, the dev server fails
immediately instead of silently picking the next port. This prevents accidental port drift that breaks API proxy
configuration.

### agent-orchestrator local dev (port 8026)

The agent-orchestrator is **operator tooling** — not a trading service. It doesn't use `dev-start.sh` or the standard QG
pipeline. Start it directly:

```bash
cd agent-orchestrator

# One-time setup (per-repo .venv via uv)
uv venv && uv sync
.venv/bin/pre-commit install --install-hooks
cd dashboard && npm install && cd ..

# Boot: backend on :8026, Vite dashboard on :5173
scripts/dev.sh            # live mode (real state.db)
scripts/dev.sh --mock     # demo mode (state.mock.db + admin endpoints)
```

Quality gates: `bash scripts/check.sh` (ruff + basedpyright + prettier + tsc). Cloud Run deploy uses `PORT=8080`
internally (set in Dockerfile); local dev uses 8026 per workspace port registry.

Dashboard public URLs: `https://agent-orchestrator.odum-research.com` (prod, pending P5 cutover) and
`https://agent-orchestrator.staging.odum-research.com` (staging). Architecture SSOT:
`codex/04-architecture/agent-orchestrator-overview.md`.

---

## Mock Mode

Mock mode is the default for local development and requires no cloud credentials.

### Environment Variables (set automatically by dev-start.sh)

| Variable          | Mock value    | Real value                   | Purpose                                  |
| ----------------- | ------------- | ---------------------------- | ---------------------------------------- |
| `CLOUD_MOCK_MODE` | `true`        | `false`                      | APIs return realistic mock data          |
| `CLOUD_PROVIDER`  | `local`       | `gcp` (or `$CLOUD_PROVIDER`) | Cloud SDK selection                      |
| `RUNTIME_MODE`    | `local`       | `production`                 | Runtime behavior selection               |
| `DISABLE_AUTH`    | `true`        | (not set)                    | Bypass authentication for local dev      |
| `MOCK_STATE_MODE` | `interactive` | `deterministic` (ci)         | State persistence in `.local-dev-cache/` |

### What mock mode provides

- Every API endpoint returns realistic, deterministic mock data.
- No cloud SDK calls (GCS, PubSub, BigQuery, Secret Manager) — all intercepted by mock layer.
- Authentication is disabled — no OAuth tokens needed.
- UIs display a `LOCAL + MOCK` badge (via `CloudModeBadge` from `@unified-trading/ui-kit`) so mock mode is always
  visually obvious.

### Running tests in mock mode

Tests always run credential-free. Quality gates automatically set `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`:

```bash
cd <repo> && bash scripts/quality-gates.sh
```

See `06-coding-standards/README.md` (Test Infrastructure: Emulators & Mocks) for the full mock/emulator matrix.

### Stateful Mock Data (MockStateStore)

By default, mock mode is **stateless** — POST/PUT endpoints return success but subsequent GETs return the same static
seed data. The `MockStateStore` (from `unified-trading-library`) adds **stateful** mock mode so mutations persist within
a dev session.

**How it works:**

1. Each API seeds its store with data from `mock_data.py` on startup.
2. POST/PUT/DELETE mutations are recorded in `.local-dev-cache/{service_name}/{collection}.jsonl`.
3. GET requests merge seed data with mutations, excluding deleted items.
4. State survives API restarts within a session (JSONL files on disk).
5. `dev-stop.sh --clean` or `dev-start.sh --reset` wipes the cache for a fresh start.

**Usage in an API route:**

```python
from unified_trading_library import MockStateStore

store = MockStateStore("deployment-api")
store.seed("deployments", MOCK_DEPLOYMENTS)  # from mock_data.py

# GET /deployments
items = store.list("deployments")

# POST /deployments
created = store.create("deployments", new_item)

# PUT /deployments/{id}
updated = store.update("deployments", item_id, fields)

# DELETE /deployments/{id}
deleted = store.delete("deployments", item_id)
```

**Cache location:** `{workspace_root}/.local-dev-cache/` (gitignored, ephemeral).

**Clearing state:**

```bash
# Clear cache and stop servers
bash unified-trading-pm/scripts/dev/dev-stop.sh --clean

# Clear cache before starting
bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock --reset
```

---

## Stopping and Cleanup

```bash
# Stop all dev servers
bash unified-trading-pm/scripts/dev/dev-stop.sh

# Stop a specific service
bash unified-trading-pm/scripts/dev/dev-stop.sh deployment-ui

# Stop all and clean mock state cache
bash unified-trading-pm/scripts/dev/dev-stop.sh --clean

# Check what is running
bash unified-trading-pm/scripts/dev/dev-status.sh
```

PID files and logs are stored in `/tmp/unified-dev-pids/`. The stop script sends SIGTERM first, waits up to 2 seconds,
then SIGKILL if needed. Logs per service: `/tmp/unified-dev-pids/<service>.log`.

---

## Smoke Testing

Verify UIs build without starting a dev server:

```bash
cd <ui-repo>
VITE_MOCK_API=true npx vite build
```

This catches TypeScript/import errors without needing a running API backend. All UI quality gates (`base-ui.sh`) include
a build check.

---

## Zombie Process Prevention

### Vitest (UI tests)

All UI repos use these vitest settings to prevent zombie node processes:

```ts
// vitest.config.ts
export default defineConfig({
  test: {
    pool: "forks", // process isolation — prevents shared-state leaks
    teardownTimeout: 5000, // kill workers that hang during teardown
  },
});
```

The `pool: "forks"` setting is mandatory. The default `threads` pool can leave orphan workers if a test crashes.

### Non-interactive test runs

Quality gates and CI use:

```bash
CI=true npm test -- --run
```

The `--run` flag prevents vitest from entering watch mode. `CI=true` ensures non-interactive behavior.

### Detecting zombie processes

```bash
# Find orphaned vitest workers
ps aux | grep "node.*vitest" | grep -v grep

# Find orphaned Python API servers
ps aux | grep "python.*-m.*_api" | grep -v grep

# Kill all dev server processes (dev-stop.sh does this automatically)
bash unified-trading-pm/scripts/dev/dev-stop.sh
```

---

## Hot Reload

### UIs (Vite HMR)

All UIs use Vite's Hot Module Replacement. File changes are reflected in the browser instantly without a full page
reload. No configuration needed — Vite HMR is enabled by default.

### APIs (uvicorn --reload)

API servers started with `RUNTIME_MODE=local` use uvicorn's `--reload` flag. Python file changes trigger an automatic
server restart. This is handled by each API's entry module — no manual flag needed when using `dev-start.sh`.

---

## DeFi Fork Testing (Tenderly Virtual TestNet)

For DeFi protocol testing (Aave, Uniswap, Morpho, etc.), the system supports mainnet fork execution via Tenderly.

### Deterministic Fork Fixture

A pinned fork is available for reproducible tests and historical replay:

| Property      | Value                                        |
| ------------- | -------------------------------------------- |
| Network       | Ethereum Mainnet                             |
| Block         | 24,681,163                                   |
| Date pinned   | 2026-03-18                                   |
| Chain ID      | 73571 (Tenderly virtual)                     |
| Sync          | Disabled (fully deterministic)               |
| SM secret     | `tenderly-fork-rpc-url`                      |
| Tenderly slug | `uts-deterministic-eth-mainnet-blk-24681163` |

Use this fork for:

- Strategy backtests that need real on-chain state (Aave reserve data, Uniswap pool liquidity, token balances)
- Gas cost estimation (exact `gasUsed` from real EVM execution)
- Flash loan atomicity testing (reverts behave identically to mainnet)
- Integration tests that validate smart contract interactions

### FORK_MODE

Set `FORK_MODE` to route DeFi protocol connectors (UDEI) to the appropriate RPC:

```bash
# Deterministic fork (pinned block — reads tenderly-fork-rpc-url from SM)
FORK_MODE=tenderly

# Local Anvil fork (run `anvil --fork-url <alchemy_url>` first)
FORK_MODE=anvil DEFI_RPC_URL=http://localhost:8545

# Production mainnet (real execution — uses Alchemy RPC)
FORK_MODE=
```

Resolution logic: `execution-service (formerly unified-defi-execution-interface)/protocols/base.py:get_defi_rpc_url()`.

### Creating a Fresh Fork (Live Paper Trading)

For paper trading against current mainnet state, create a new fork at latest block:

```bash
TENDERLY_KEY=$(gcloud secrets versions access latest --secret=tenderly-api-key)
curl -s -X POST "https://api.tenderly.co/api/v1/account/me/project/project/vnets" \
  -H "X-Access-Key: $TENDERLY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "uts-live-session-'$(date +%Y%m%d-%H%M)'",
    "display_name": "UTL Live Session '$(date +%Y-%m-%d %H:%M)'",
    "fork_config": {"network_id": 1, "block_number": "latest"},
    "virtual_network_config": {"chain_config": {"chain_id": 73571}},
    "sync_state_config": {"enabled": false}
  }'
```

Extract the Admin RPC URL from the response `rpcs` array and pass as `DEFI_RPC_URL`.

---

## Demo Mode (Full Seeded Stack)

For a pre-seeded local stack with sample data (instruments, features, mock market data):

```bash
bash unified-trading-pm/scripts/demo-mode.sh --seed
```

This starts GCP emulators (Pub/Sub, fake-GCS-server, BigQuery emulator), seeds reference data, and launches the API
layer. No cloud credentials required.

---

## Command Reference

| What you want to do         | Command                                                  | Mode     | Cache behavior                                |
| --------------------------- | -------------------------------------------------------- | -------- | --------------------------------------------- |
| Start full stack (no creds) | `dev-start.sh --all --mode mock`                         | mock     | Interactive — persists to `.local-dev-cache/` |
| Start for CI/headless       | `dev-start.sh --all --mode ci`                           | ci       | Deterministic — no persistence                |
| Start with real APIs        | `dev-start.sh --all --mode api-real`                     | api-real | N/A — real cloud data                         |
| Start staging-like          | `dev-start.sh --all --mode real`                         | real     | N/A — real cloud data                         |
| Start single stack          | `dev-start.sh --stack deployment --mode mock`            | mock     | Interactive                                   |
| Stop all servers            | `dev-stop.sh`                                            | —        | Cache preserved                               |
| Stop + wipe cache           | `dev-stop.sh --clean`                                    | —        | Cache deleted                                 |
| Start fresh (wipe + start)  | `dev-start.sh --all --mode mock --reset`                 | mock     | Cache wiped before start                      |
| Check running services      | `dev-status.sh`                                          | —        | Shows all 5 mode axes                         |
| List all stacks/ports       | `dev-start.sh --list`                                    | —        | —                                             |
| Run Python quality gates    | `cd <repo> && bash scripts/quality-gates.sh`             | —        | Per-repo .venv                                |
| Run UI tests (headless)     | `cd <ui-repo> && CI=true npm test -- --run`              | —        | —                                             |
| UI smoke build              | `cd <ui-repo> && VITE_MOCK_API=true npx vite build`      | —        | —                                             |
| Kill zombie processes       | `dev-stop.sh` (or manual: `ps aux \| grep node.*vitest`) | —        | —                                             |

All `dev-*.sh` scripts live in `unified-trading-pm/scripts/dev/`.

---

## Frontend-Backend Integration Architecture

### Architecture: Direct Sibling Calls

The UI calls backend services running locally in the same workspace. No Docker, no BFF, no deployments needed for
development.

```
┌─────────────────────────────┐     ┌──────────────────────────────┐
│  unified-trading-system-ui  │     │  unified-trading-api         │
│  (Next.js, port 3000;       │────▶│  (FastAPI, port 8030)        │
│   real-API server :3100)    │     │                              │
│                             │     │  CLOUD_MOCK_MODE=true        │
│  next.config.mjs rewrites  │     │  seed_all_domains() on       │
│  /api/* → localhost:8030    │     │  startup provides mock       │
│                             │     │  data for all 16 domains     │
└─────────────────────────────┘     └──────────────────────────────┘
```

### Data Flow

1. **Registry data** (venues, instruments, enums): Generated offline from UAC → `ui-reference-data.json` → TypeScript
   constants. No runtime API call needed.

2. **Schema types**: Generated from `openapi.json` via `npm run generate:types` → `lib/types/api-generated.ts` (20K
   lines, 298 endpoints). Regenerate when API changes.

3. **Domain data** (positions, orders, risk, alerts, etc.): Live API calls via React Query hooks. In mock mode,
   `unified-trading-api` returns seeded data from `seed_all_domains()`. In real mode, it reads from cloud storage.

### Quick Start

```bash
# Terminal 1: Start the API in mock mode
cd unified-trading-api
CLOUD_MOCK_MODE=true DISABLE_AUTH=true python -m unified_trading_api.main

# Terminal 2: Start the UI
cd unified-trading-system-ui
npm run dev

# Or use the dev script for the full stack:
bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock
```

### Regenerating Types

When API endpoints change:

```bash
# 1. Regenerate OpenAPI spec from the API
cd unified-trading-api && python -m scripts.export_openapi

# 2. Copy to UI and generate types
cp openapi.json ../unified-trading-system-ui/lib/registry/openapi.json
cd ../unified-trading-system-ui && npm run generate:types
```

### Why Not BFF / Docker / Deployed Services?

- **BFF**: Adds a middleware layer with no value — the API already handles auth, pagination, error shapes.
- **Docker**: Slow build/restart cycle for iterative development.
- **Deployed services**: 30-60s deploy latency per change. Unusable for rapid dev.
- **Direct localhost**: Sub-second hot reload on both UI (Next.js) and API (uvicorn --reload).

---

---

## Testing — Credential-Free Rules and Emulator Ports

All tests run credential-free. Quality gates automatically set `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`. Use
`pytest --block-network` to enforce no outbound calls during unit tests.

### GCP Emulator Ports

| Service         | Emulator address      |
| --------------- | --------------------- |
| **Pub/Sub**     | `localhost:8085`      |
| **GCS (Storage)** | `localhost:4443`    |
| **BigQuery**    | `localhost:9050`      |

These are started automatically by `demo-mode.sh --seed` and the quality-gate emulator fixture. Configure them via
`PUBSUB_EMULATOR_HOST`, `STORAGE_EMULATOR_HOST`, and `BIGQUERY_EMULATOR_HOST` respectively.

### AWS Mocking

AWS calls use **moto** with the `@mock_aws` decorator — no real AWS credentials needed:

```python
from moto import mock_aws

@mock_aws
def test_s3_upload():
    ...
```

### Cassette Parity (VCR)

After every commit that touches `unified-api-contracts`, run the cassette parity test to confirm all recorded HTTP
cassettes match the current schema:

```bash
cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py
```

This must pass on every commit — stale cassettes are caught here, not at runtime.

### DeFi Integration: Tenderly Conftest Path

DeFi integration tests that require a fork use fixtures defined in:

```
execution-service/tests/defi_execution/integration/conftest.py
```

This conftest sets up the Tenderly fork (pinned block 24,681,163) for the full `defi_execution` integration suite. See
the **DeFi Fork Testing** section above for fork configuration details.

### basedpyright — Per-Repo Only, Never Workspace Root

**Never run `basedpyright .` from the workspace root.** Each subdirectory is an independent git repo with its own
`pyproject.toml` / `pyrightconfig.json` configuration. Running from the root crosses repo boundaries, produces
misleading cross-repo errors, and can time out on the combined source tree. Always scope to the target repo:

```bash
cd <repo> && run_timeout 120 basedpyright <source_dir>/
```

Use `basedpyright`, not `pyright` — the workspace enforces strict settings
(`reportAny`/`reportUnknownMemberType`/`reportUnknownVariableType` = error).

---

## Cross-References

- Testing infrastructure (emulators, mocks, cassettes): `06-coding-standards/README.md` (Test Infrastructure)
- UI branding and shared components: `06-coding-standards/ui-branding.md`
- UI dependency matrix and API wiring: `05-infrastructure/ui-dependency-matrix.md`
- Quality gates: `06-coding-standards/quality-gates.md`
- Workspace bootstrap (fresh machine): `unified-trading-pm/scripts/workspace/workspace-bootstrap.sh`
- Per-repo dev setup: `scripts/setup.sh` in each repo (template: `06-coding-standards/setup-standards.md`)
