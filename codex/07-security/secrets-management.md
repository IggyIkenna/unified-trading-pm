---
doc_type: codex-ssot
title: Secrets Management
summary: >-
  Secrets management SSOT: runtime access via `get_secret_client()` (GCP/AWS by `CLOUD_PROVIDER`, no env-var fallback),
  the `.env.example` + config-class pattern, the full Secret Manager inventory (vendor/exchange/execution/service-auth
  keys with VCR status), IAM bindings, and Docker/hardcoding prevention.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [client-reporting-api, execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: [secrets, cefi, defi, tradfi, sports, data-vendor]
related:
  [
    /codex/07-security/secret-naming-convention.md,
    /codex/07-security/client-credentials.md,
    /codex/02-data/vcr-cassette-ownership.md,
  ]
created: 2026-03-27
authoritative_for: [get_secret_client secret access pattern, Secret Manager key inventory]
referenced_by:
  [
    /codex/04-architecture/cloud-agnostic-migration.md,
    /codex/04-architecture/mev-protection.md,
    /codex/07-security/audit-logging.md,
    /codex/07-security/client-credentials.md,
    /codex/07-security/dependency-scanning.md,
    /codex/07-security/secret-naming-convention.md,
    /codex/07-security/secret-rotation.md,
    /codex/07-security/testing-with-api-keys.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Secrets Management

## TL;DR

- **All secrets are accessed at runtime** via `get_secret_client()` from `unified_cloud_interface` (T0 library). No
  secrets in code, images, or build-time env vars.
- **GCP Secret Manager** is the primary backend (project: `my_project_id`). AWS Secrets Manager is the secondary
  backend. The `CLOUD_PROVIDER` env var selects which.
- **`.env.example` pattern**: every service has a `.env.example` that documents required environment variables with
  placeholder values. Actual values are never committed.
- **No hardcoded identifiers**: project IDs, bucket names, and API keys are config fields on
  `UnifiedCloudServicesConfig`, not string literals in source code.
- **Secret naming convention**: `{service}-{purpose}` or `{client}-{venue}-{credential-type}` for consistent discovery
  and access control.
- **Secret rotation**: [PLANNED — post-cutover]. Currently manual. Target: automated rotation with zero-downtime
  credential swap.
- **Provider manifest**: `unified-api-contracts/unified_api_contracts/config/provider_api_versions.yaml` is SSOT for API
  keys, testnet availability, and data_type per provider. When adding a provider or key, update the manifest first. See
  `.cursor/rules/config/provider-manifest-ssot.mdc` and Plan 6 (UAC Residual Refactors).

---

## Secret Access Pattern [IMPLEMENTED]

### get_secret_client()

The canonical way to access secrets in the Unified Trading System:

> **Import from T0:** `unified_cloud_interface` is a Tier 0 library with no inter-library dependencies. All cloud I/O
> (storage, secrets, queues) is accessed via its factory functions.

```python
from unified_cloud_interface import get_secret_client

# Automatically selects GCP Secret Manager or AWS Secrets Manager
# based on CLOUD_PROVIDER environment variable
secret_client = get_secret_client()

# Access a secret by name
api_key = secret_client.access_secret("client-alpha-binance-key")
api_secret = secret_client.access_secret("client-alpha-binance-secret")
```

### What Happens Under the Hood

```
get_secret_client()
  |
  |-- Check CLOUD_PROVIDER env var
  |
  |-- If "gcp":
  |     |-- GcpSecretClient(project_id=config.gcp_project_id)
  |     |-- Uses google.cloud.secretmanager.SecretManagerServiceClient
  |     |-- Path: projects/{project}/secrets/{name}/versions/latest
  |
  |-- If "aws":
  |     |-- AwsSecretClient(region=config.aws_region)
  |     |-- Uses boto3 secretsmanager client
  |     |-- Path: arn:aws:secretsmanager:{region}:{account}:secret:{name}
```

### Anti-Patterns (Never Do This)

```python
# WRONG: Direct GCP import
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()

# WRONG: Hardcoded secret path
secret = client.access_secret_version(
    name="projects/test-project/secrets/my-key/versions/latest"
)

# WRONG: Secret in source code
API_KEY = "sk-abc123..."

# WRONG: Hardcoded placeholder string (will reach production as-is)
KILL_SWITCH_API_KEY = "change-me-in-production"

# WRONG: Import from deleted unified_trading_services.auth
from unified_trading_services.auth import GoogleOIDCAuth  # module deleted Feb 2026

# WRONG: Secret in environment variable at build time
# (Dockerfile ARG or Cloud Build substitution)
ARG API_KEY
ENV API_KEY=$API_KEY

# WRONG: os.getenv for secrets
api_key = os.getenv("BINANCE_API_KEY", "")
```

---

## Unified config ↔ unified cloud — package import order [IMPLEMENTED]

### Why this exists

While `unified_cloud_interface` is still executing its package `__init__.py`, it may import submodules (for example
`api_auth`) that do `from unified_config_interface import UnifiedCloudConfig`. That loads
`unified_config_interface/__init__.py`, which in turn imports credential helper modules. If a helper does
`from unified_cloud_interface import CredentialsRegistry, get_secret` (or similar) **at module top level**, Python tries
to finish loading `unified_cloud_interface` before it is ready →
`ImportError: cannot import name 'CredentialsRegistry' from partially initialized module 'unified_cloud_interface'`.

This is an **import-time cycle**, not a tier-design mistake: secret **names** still belong in
`unified_cloud_interface/credentials_registry.py`; credential **schemas and getters** stay in `unified-config-interface`
next to other venue config patterns.

### Rule (required)

Any `unified-config-interface` module that calls `get_secret` or uses `CredentialsRegistry` must import those symbols
**inside the function** that performs the fetch (lazy import), never at module scope. Reference:
`unified_config_interface/ibkr_credentials.py` — `get_ibkr_credentials()` imports cloud there.

### Optional hardening

- Keep heavy or optional credential helpers from widening the default `unified_config_interface` public surface if not
  every consumer needs them; lazy imports in getters are the primary fix.
- On the cloud side, deferring config imports inside `api_auth` (lazy) is a secondary lever if new cycles appear.

### Mock mode and optional keys

When `UnifiedCloudConfig.is_mock_mode()` is true (`DATA_MODE=mock` / legacy `CLOUD_MOCK_MODE`), services must **not**
require resolution of external provider secrets (for example Tardis) for startup. See
`09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md` for the full mode axis SSOT.

### Dev-only CLI dependencies

Imports such as `uvicorn` for a `--serve` code path belong **inside that branch** so quality gates and workers that
never run the server do not need the package installed at import time.

---

## .env.example Pattern [IMPLEMENTED]

Every service maintains a `.env.example` file that documents required environment variables **without actual values**:

```bash
# .env.example -- copy to .env and fill in values
# NEVER commit .env with actual values

# Cloud provider selection
CLOUD_PROVIDER=gcp

# GCP project (for Secret Manager, GCS, BigQuery)
GCP_PROJECT_ID=your-project-id

# Service-specific configuration
CATEGORY=CEFI
VENUE=BINANCE-FUTURES
LOG_LEVEL=INFO

# Data vendor API keys are in Secret Manager, not here
# Access via: get_secret_client().access_secret("tardis-api-key")
```

### Rules

| Rule                                          | Rationale                                               |
| --------------------------------------------- | ------------------------------------------------------- |
| `.env.example` is committed to git            | Documents what env vars a service needs                 |
| `.env` is in `.gitignore`                     | Contains actual values, never committed                 |
| No actual secret values in `.env.example`     | Prevents accidental exposure                            |
| Comments explain where secrets come from      | Developers know to use Secret Manager                   |
| All env vars are also defined in config class | Single source of truth via `UnifiedCloudServicesConfig` |

### Config Class Integration

Environment variables from `.env` are consumed by the service's config class, not by `os.getenv()`:

```python
from unified_config_interface import UnifiedCloudConfig
from pydantic import Field, AliasChoices

class InstrumentsConfig(UnifiedCloudConfig):
    category: str = Field(
        default="CEFI",
        validation_alias=AliasChoices("CATEGORY", "ASSET_CATEGORY"),
    )
    venue: str = Field(
        default="BINANCE-FUTURES",
        validation_alias=AliasChoices("VENUE", "EXCHANGE"),
    )
    # No secret fields here -- secrets come from Secret Manager at runtime
```

---

## Secret Categories

### Infrastructure Secrets [IMPLEMENTED]

Secrets used by CI/CD and deployment infrastructure:

| Secret Name        | Purpose                                 | Used By            |
| ------------------ | --------------------------------------- | ------------------ |
| `github-token`     | Clone private repos in Cloud Build      | Cloud Build steps  |
| `gh-pat`           | GitHub Actions checkout of private deps | GitHub Actions     |
| `terraform-sa-key` | Terraform service account credentials   | Deployment scripts |

### Data Vendor API Keys

Secrets for external data providers. **This table is the SSOT** — verified against
`gcloud secrets list --project=test-project` on 2026-02-27.

**VCR Status legend:**

- `KEY_IN_SM` — secret confirmed in Secret Manager; cassette not yet recorded
- `VALIDATED` — cassette recorded and tests pass
- `KEY_NOT_IN_SM` — no key; procurement/access required before cassette can be recorded
- `NO_VCR` — not HTTP-based; VCR not applicable

The `get_secret_client` pattern:

```python
from unified_cloud_interface import get_secret_client

api_key = get_secret_client(
    secret_name="<secret-name>",       # column 2 below
    project_id=config.gcp_project_id,
)
```

#### Market Data Vendors

| Secret Name(s) in SM                                                                             | Env Var Fallback    | Purpose                                                         | Key in SM?          | VCR Status                              |
| ------------------------------------------------------------------------------------------------ | ------------------- | --------------------------------------------------------------- | ------------------- | --------------------------------------- |
| `tardis-api-key` (+ `tardis-api-key-full`, `tardis-api-key-backup`)                              | `TARDIS_API_KEY`    | Tardis.dev historical tick data (CSV.GZ batch files)            | ✅ Yes              | `KEY_IN_SM` — cassette not recorded     |
| `databento-api-key`, `databento-api-key-1` … `databento-api-key-20`, `databento-alt-api-key-1/2` | `DATABENTO_API_KEY` | Databento market data — pool of 22 keys, rotated by `key_index` | ✅ Yes (pool of 22) | `KEY_IN_SM` — cassette not recorded     |
| `fred-api-key`                                                                                   | `FRED_API_KEY`      | FRED macroeconomic time series                                  | ✅ Yes              | `VALIDATED` (cassette at `fred/mocks/`) |
| `envio-api-key`                                                                                  | `ENVIO_API_KEY`     | Envio blockchain indexing/streaming                             | ✅ Yes              | `KEY_IN_SM` — no cassette               |

#### On-Chain / DeFi

| Secret Name(s) in SM                                            | Env Var Fallback    | Purpose                                                                                                                                                                       | Key in SM?                  | VCR Status                                                |
| --------------------------------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | --------------------------------------------------------- |
| `thegraph-api-key`, `thegraph-api-key-2` … `thegraph-api-key-9` | `THE_GRAPH_API_KEY` | The Graph subgraph queries — pool of 9 keys, round-robin sharding                                                                                                             | ✅ Yes (pool of 9)          | `KEY_IN_SM` — cassette not recorded                       |
| `alchemy-api-key`                                               | `ALCHEMY_API_KEY`   | Alchemy node RPC (Ethereum, DeFi protocols)                                                                                                                                   | ✅ Yes                      | `KEY_IN_SM` — REST cassette not recorded (WS mock exists) |
| `aavescan-api-key`                                              | `AAVESCAN_API_KEY`  | Aavescan DeFi analytics                                                                                                                                                       | ✅ Yes                      | `KEY_IN_SM` — no cassette                                 |
| `aws-hyperliquid-s3`                                            | n/a                 | AWS IAM credentials (JSON: `aws_access_key_id`, `aws_secret_access_key`, `region`) for Hyperliquid requester-pays S3 archives (`hyperliquid-archive`, `hl-mainnet-node-data`) | ✅ Yes — **ACTIVE, in use** | `NO_VCR` (S3/boto3, not HTTP API)                         |

> **`graph-api-key`** also exists in SM — this is the **deprecated** old name. Use `thegraph-api-key`. Delete
> `graph-api-key` once all consumers are confirmed to use the new name.

> **Env var fix required:** `uniswapv2_adapter.py` and `uniswapv4_adapter.py` use `THEGRAPH_API_KEY` — must be changed
> to `THE_GRAPH_API_KEY`.

#### Hyperliquid Execution (Agent Wallet)

| Secret Name             | Format                                                                              | Purpose                                                                                                                                                                                                          | Key in SM?                  |
| ----------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| `hyperliquid-trade-key` | JSON: `{"private_key": "0x...", "wallet_address": "0x...", "main_wallet": "0x..."}` | Hyperliquid API agent wallet private key — used for EIP-712 signing of orders. Agent wallet `0x75c8e18dF5864BE8fBF0e3265be782Ec7d5c6C25` authorized by main wallet `0x992ebFe04DB05f964C45BCE3D73Ca4c81715a79f`. | ✅ Yes (created 2026-02-27) |

> **Note:** Hyperliquid uses EIP-712 signing, not API keys. The agent wallet is a separate keypair authorized in the
> Hyperliquid UI. Read-only endpoints (clearinghouse state, fills, orders) only need the public wallet address — no
> private key.

---

#### Centralized Exchange (Market Data — Read Keys)

These are **market data** read keys, not execution keys. Binance and Deribit have separate read and trade keys.

| Secret Name(s) in SM                                   | Env Var Fallback          | Purpose                                          | Key in SM?                                                                                                                                                                                | VCR Status                                                    |
| ------------------------------------------------------ | ------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `binance-read-api-key` + `binance-read-api-key-secret` | `BINANCE_READ_API_KEY`    | Binance read-only market data key                | ✅ Yes                                                                                                                                                                                    | `KEY_IN_SM` — private WS cassette not recorded (WS, not HTTP) |
| `deribit-read-api-key` + `deribit-read-api-key-secret` | `DERIBIT_READ_API_KEY`    | Deribit read-only market data key                | ✅ Yes                                                                                                                                                                                    | `KEY_IN_SM` — private WS cassette not recorded (WS, not HTTP) |
| `coinbase-api-key`                                     | `COINBASE_API_KEY`        | Coinbase brokerage orders                        | ❌ No                                                                                                                                                                                     | `KEY_NOT_IN_SM`                                               |
| ~~`hyperliquid-api-key`~~                              | ~~`HYPERLIQUID_API_KEY`~~ | ~~Hyperliquid private user-state REST endpoint~~ | **Not needed** — Hyperliquid public REST API requires no auth. Historical data uses `aws-hyperliquid-s3` (AWS IAM). Trading/execution would use wallet signing (EIP-712), not an API key. | n/a                                                           |

#### Centralized Exchange (Execution — Trade Keys)

| Secret Name(s) in SM                                     | Env Var Fallback        | Purpose                     | Key in SM?                                                  | Notes                                                   |
| -------------------------------------------------------- | ----------------------- | --------------------------- | ----------------------------------------------------------- | ------------------------------------------------------- |
| `binance-trade-api-key` + `binance-trade-api-key-secret` | `BINANCE_TRADE_API_KEY` | Binance trade execution key | ✅ Yes                                                      | Used by execution-service                               |
| `deribit-trade-api-key` + `deribit-trade-api-key-secret` | `DERIBIT_TRADE_API_KEY` | Deribit trade execution key | ✅ Yes                                                      | Used by execution-service                               |
| `bybit_api_key` + `bybit_api_secret`                     | `BYBIT_API_KEY`         | Bybit trade execution key   | ✅ Yes (**naming violation** — uses underscore, not hyphen) | Must be renamed to `bybit-api-key` + `bybit-api-secret` |

> **`bybit_api_key` naming violation:** Secret Manager name uses underscore. Convention requires hyphens. Rename to
> `bybit-api-key` + `bybit-api-secret` when safe (notify any consumers before deletion).

#### Execution (Testnet / Staging)

| Secret Name                          | Env Var Fallback                     | Purpose                 | Key in SM?                              | VCR Status            |
| ------------------------------------ | ------------------------------------ | ----------------------- | --------------------------------------- | --------------------- |
| `binance-futures-testnet-api-key`    | `BINANCE_FUTURES_TESTNET_API_KEY`    | Binance Futures testnet | ❌ No (not in SM — use env var locally) | integration test only |
| `binance-futures-testnet-api-secret` | `BINANCE_FUTURES_TESTNET_API_SECRET` | Binance Futures testnet | ❌ No                                   | integration test only |

#### Sports Betting / Prediction Markets

| Secret Name         | Env Var Fallback    | Purpose                                                    | Key in SM?                               | VCR Status                                   |
| ------------------- | ------------------- | ---------------------------------------------------------- | ---------------------------------------- | -------------------------------------------- |
| `pinnacle-api-key`  | `PINNACLE_API_KEY`  | Pinnacle sports odds API                                   | ❌ No                                    | `KEY_NOT_IN_SM`                              |
| `odds-api-key`      | `ODDS_API_KEY`      | The Odds API (sports odds aggregator)                      | ❌ No                                    | `KEY_NOT_IN_SM`                              |
| `betfair-api-key`   | `BETFAIR_API_KEY`   | Betfair exchange (Application Key) — sports odds/execution | ✅ Provision via `setup_secret.sh`       | `KEY_IN_SM` once provisioned                 |
| `kalshi-api-key`    | `KALSHI_API_KEY`    | Kalshi prediction market portfolio                         | ❌ No                                    | `KEY_NOT_IN_SM`                              |
| `smarkets-api-key`  | `SMARKETS_API_KEY`  | Smarkets sports betting exchange                           | ❌ No                                    | `KEY_NOT_IN_SM`                              |
| `betdaq-api-key`    | `BETDAQ_API_KEY`    | Betdaq betting exchange                                    | ❌ No                                    | `KEY_NOT_IN_SM`                              |
| `matchbook-api-key` | `MATCHBOOK_API_KEY` | Matchbook betting exchange                                 | ❌ No (cassette exists, public endpoint) | `VALIDATED` (cassette at `matchbook/mocks/`) |
| `oddspapi-api-key`  | `ODDSPAPI_API_KEY`  | OddsPapi odds aggregator (single key)                      | ✅ Yes                                   | `KEY_IN_SM`                                  |
| `oddspapi-api-keys` | `ODDSPAPI_API_KEYS` | OddsPapi key pool (JSON array, 17 keys, 4,250 req/mo)      | ✅ Yes                                   | `KEY_IN_SM`                                  |

> **⚠️ endpoint_registry.py correction needed:** The notes for `pinnacle`, `odds_api`, `betfair`, `kalshi` claim
> "confirmed in Secret Manager" — this is **incorrect**. None of these keys exist in SM. Status should be
> `BLACKLISTED_NO_ACCESS` not `PENDING_CASSETTE_AWAITING_AUTH`.

#### Alternative Data

| Secret Name            | Env Var Fallback       | Purpose                                      | Key in SM? | VCR Status                                                      |
| ---------------------- | ---------------------- | -------------------------------------------- | ---------- | --------------------------------------------------------------- |
| `api-football-api-key` | `API_FOOTBALL_API_KEY` | API-Football leagues/fixtures/stats          | ❌ No      | `KEY_NOT_IN_SM`                                                 |
| `openbb-fmp-api-key`   | `OPENBB_FMP_API_KEY`   | OpenBB / Financial Modeling Prep market data | ✅ Yes     | `KEY_IN_SM` — no cassette                                       |
| `openbb-fred-api-key`  | `OPENBB_FRED_API_KEY`  | OpenBB / FRED macroeconomic data via OpenBB  | ✅ Yes     | `KEY_IN_SM` — no cassette (separate from direct `fred-api-key`) |
| `glassnode-api-key`    | `GLASSNODE_API_KEY`    | Glassnode on-chain analytics                 | ❌ No      | `KEY_NOT_IN_SM`                                                 |

#### Traditional Finance

| Secret Name    | Env Var Fallback | Purpose                 | Key in SM? | VCR Status                               |
| -------------- | ---------------- | ----------------------- | ---------- | ---------------------------------------- |
| `ibkr-tws-key` | `IBKR_TWS_KEY`   | Interactive Brokers TWS | ❌ No      | `NO_VCR` (TWS socket protocol, not HTTP) |

> **⚠️ endpoint_registry.py correction needed:** `ibkr` is marked `PENDING_CASSETTE_AWAITING_AUTH` with notes claiming
> credentials confirmed — key does not exist in SM.

#### Service Authentication

Secrets required for intra-service API authentication (Google OAuth, kill-switch).

| Secret Name                             | Env Var Fallback         | Purpose                                                                                                                                                                                      | Key in SM?        |
| --------------------------------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| `google-oauth-client-id`                | `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth 2.0 client ID used by `GoogleOIDCAuth` (execution-service) and `GoogleOAuthMiddleware` (client-reporting-api). Loaded via `get_secret_client` at startup — **never hardcoded**. | ❌ Must provision |
| `execution-service-kill-switch-api-key` | `KILL_SWITCH_API_KEY`    | API key for `/kill-switch/activate` and `/kill-switch/deactivate` endpoints in execution-service. Loaded via `get_secret_client` — **replaces hardcoded `"change-me-in-production"`**.       | ❌ Must provision |

**Wiring pattern** (canonical — no fallback string literals):

```python
_GCP_PROJECT_ID: str = os.environ["GCP_PROJECT_ID"]  # fail loud if not set

KILL_SWITCH_API_KEY: str = get_secret_client(
    project_id=_GCP_PROJECT_ID,
    secret_name="execution-service-kill-switch-api-key",
)
_GOOGLE_OAUTH_CLIENT_ID: str = get_secret_client(
    project_id=_GCP_PROJECT_ID,
    secret_name="google-oauth-client-id",
)
```

**Auth class location:** `GoogleOIDCAuth` and `GoogleOAuthMiddleware` are **service-local**
(`execution_service/auth.py`, `client_reporting_api/auth.py`). They were removed from `unified_trading_services.auth`
(deleted Feb 2026). Do not import auth classes from `unified_trading_services`.

#### Infrastructure / Tooling

| Secret Name                                               | Purpose                                     | Key in SM? |
| --------------------------------------------------------- | ------------------------------------------- | ---------- |
| `github-token`                                            | Clone private repos in Cloud Build          | ✅ Yes     |
| `github-automation-token`                                 | Automation workflows                        | ✅ Yes     |
| `cursor-api-key`                                          | Cursor AI API                               | ✅ Yes     |
| `clickup-api-key`                                         | ClickUp project management API              | ✅ Yes     |
| `redis-host`, `redis-password`, `redis-port`, `redis-url` | Redis cluster connection (added 2026-02-26) | ✅ Yes     |

#### Multi-Venue via CCXT

| Secret Pattern       | Env Var Pattern      | Purpose                                   | Key in SM?               |
| -------------------- | -------------------- | ----------------------------------------- | ------------------------ |
| `{venue}-api-key`    | `{VENUE}_API_KEY`    | CCXT exchange API key (dynamic per venue) | Varies — check per-venue |
| `{venue}-api-secret` | `{VENUE}_API_SECRET` | CCXT exchange API secret                  | Varies                   |

#### Sports Betting Services Repo (separate repo — violations to fix)

These APIs are used in `sports-betting-services/` repo and currently accessed via raw `os.getenv()` — not yet integrated
with Secret Manager. Must be migrated.

| Target Secret Name             | Env Var                        | Purpose                                                          | Migration Status         |
| ------------------------------ | ------------------------------ | ---------------------------------------------------------------- | ------------------------ |
| `soccer-football-info-api-key` | `SOCCER_FOOTBALL_INFO_API_KEY` | Soccer Football Info API                                         | NOT MIGRATED (violation) |
| `footystats-api-key`           | `FOOTYSTATS_API_KEY`           | Footystats API                                                   | NOT MIGRATED (violation) |
| `odds-api-key`                 | `ODDS_API_KEY`                 | The Odds API (shared with UMI)                                   | NOT MIGRATED (violation) |
| `google-maps-api-key`          | `GOOGLE_MAPS_API_KEY`          | Google Maps geocoding                                            | NOT MIGRATED (violation) |
| `api-football-api-key`         | `API_FOOTBALL_KEY`             | API Football (env var must be renamed to `API_FOOTBALL_API_KEY`) | NOT MIGRATED             |

### Client Exchange API Keys [IMPLEMENTED]

Per-client exchange credentials (see [client-credentials.md](./client-credentials.md)):

| Secret Pattern                | Purpose                           | Used By           |
| ----------------------------- | --------------------------------- | ----------------- |
| `{client}-{venue}-api-key`    | Exchange API key                  | execution-service |
| `{client}-{venue}-api-secret` | Exchange API secret               | execution-service |
| `{client}-{venue}-passphrase` | Exchange passphrase (if required) | execution-service |

---

## Secret Naming Convention

### Format

```
{scope}-{venue-or-service}-{credential-type}

Examples:
  client-alpha-binance-api-key
  client-alpha-binance-api-secret
  client-alpha-deribit-api-key
  tardis-api-key
  databento-api-key
  github-token
```

### Rules

| Rule                                    | Example                                                           |
| --------------------------------------- | ----------------------------------------------------------------- |
| Lowercase, hyphen-separated             | `client-alpha-binance-api-key` (not `ClientAlpha_Binance_APIKey`) |
| Client prefix for client-scoped secrets | `client-alpha-*`                                                  |
| Venue name matches canonical venue ID   | `binance`, `deribit`, `okx` (not `Binance`, `DERIBIT`)            |
| Credential type is the suffix           | `-api-key`, `-api-secret`, `-passphrase`                          |
| No version numbers in names             | Use Secret Manager versioning, not name suffixes                  |

---

## GCP Secret Manager Configuration [IMPLEMENTED]

### Project and Access

| Setting        | Value                                    |
| -------------- | ---------------------------------------- |
| GCP Project    | `test-project`                           |
| Replication    | Automatic (Google-managed)               |
| Access control | Per-secret IAM bindings                  |
| Versioning     | Enabled (latest version used by default) |

### IAM Bindings

Each service account has `roles/secretmanager.secretAccessor` only on the secrets it needs:

```hcl
# Terraform: grant execution-service access to client secrets
resource "google_secret_manager_secret_iam_member" "exec_client_key" {
  secret_id = google_secret_manager_secret.client_alpha_binance_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.execution_sa.email}"
}
```

A service cannot access secrets it has not been explicitly granted access to.

---

## Secret Rotation [PLANNED — post-cutover]

### Target Architecture

```
Rotation Trigger (scheduled or manual)
  |
  |-- 1. Generate new credential
  |       |-- For exchange keys: create new key in exchange admin panel
  |       |-- For vendor keys: request new key from vendor
  |
  |-- 2. Store new value as new version in Secret Manager
  |       |-- Old version remains active (not destroyed)
  |
  |-- 3. Restart affected services
  |       |-- Services fetch latest version on startup
  |       |-- Zero downtime: rolling restart of execution threads
  |
  |-- 4. Verify new credential works
  |       |-- Health check endpoint confirms connectivity
  |       |-- If failure: rollback to previous version
  |
  |-- 5. Disable old credential
  |       |-- After verification period (24h)
  |       |-- Mark old version as disabled in Secret Manager
  |
  |-- 6. Audit log
  |       |-- Record rotation event, who triggered, success/failure
```

### Rotation Frequency Targets

| Secret Type                | Rotation Frequency | Rationale                                   |
| -------------------------- | ------------------ | ------------------------------------------- |
| Client exchange API keys   | Every 90 days      | Balance security with operational overhead  |
| Data vendor API keys       | Every 180 days     | Lower risk (read-only, no financial impact) |
| Infrastructure credentials | Every 90 days      | Standard practice                           |
| GitHub tokens              | Every 90 days      | Standard practice                           |

### Rotation Challenges

| Challenge                                  | Mitigation                                         |
| ------------------------------------------ | -------------------------------------------------- |
| Exchange key rotation requires manual step | Document procedure; notify client in advance       |
| Service restart during active trading      | Schedule rotation during low-activity windows      |
| Key propagation delay                      | Grace period where both old and new keys are valid |
| Client coordination                        | Notification workflow before rotation              |

---

## Hardcoded Value Prevention [IMPLEMENTED]

### What Must Not Be Hardcoded

| Category     | Wrong                           | Right                                                 |
| ------------ | ------------------------------- | ----------------------------------------------------- |
| Project IDs  | `"test-project"`                | `config.gcp_project_id`                               |
| Bucket names | `"features-delta-one-cefi-..."` | `config.output_bucket` or `get_bucket_for_category()` |
| API keys     | `"sk-abc123"`                   | `get_secret_client().access_secret("key-name")`       |
| Service URLs | `"https://api.binance.com"`     | `config.exchange_base_url`                            |
| Region names | `"asia-northeast1"`             | `config.gcp_region`                                   |

### Enforcement

| Mechanism                                    | What It Catches                        | Status                   |
| -------------------------------------------- | -------------------------------------- | ------------------------ |
| Code review (PR)                             | Manual inspection for hardcoded values | [IMPLEMENTED]            |
| Quality gates (ruff)                         | Certain anti-patterns via ruff rules   | [IMPLEMENTED]            |
| `.cursorrules`                               | AI agents prevented from hardcoding    | [IMPLEMENTED]            |
| Automated secret scanning (e.g., truffleHog) | Leaked credentials in git history      | [PLANNED — post-cutover] |

---

## Docker Security [IMPLEMENTED]

### Multi-Stage Build

```dockerfile
# Stage 1: Build dependencies
FROM python:3.13-slim AS builder
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Stage 2: Runtime (no build tools, no source control)
FROM python:3.13-slim
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/...
COPY src/ /app/src/
# No secrets, no .env, no git history
```

### Image Security Rules

| Rule                                               | Rationale                               |
| -------------------------------------------------- | --------------------------------------- |
| Use `python:3.13-slim` base                        | Minimal attack surface                  |
| No `COPY .env`                                     | Secrets not baked into image            |
| No `ARG SECRET_KEY`                                | Build args are visible in image history |
| Multi-stage build                                  | Build tools not in runtime image        |
| No `RUN pip install --upgrade pip` without pinning | Reproducible builds                     |
| `.dockerignore` excludes `.env`, `.git`, `tests/`  | Only production code in image           |

---

## Implementation Status

| Component                                              | Status                   |
| ------------------------------------------------------ | ------------------------ |
| `get_secret_client()` — fail-loud, no env var fallback | [IMPLEMENTED]            |
| `.env.example` in all services                         | [IMPLEMENTED]            |
| Per-service IAM bindings for secrets                   | [IMPLEMENTED]            |
| Secret naming convention enforced                      | [IMPLEMENTED]            |
| No hardcoded values (enforced by .cursorrules)         | [IMPLEMENTED]            |
| Multi-stage Docker builds                              | [IMPLEMENTED]            |
| Secret rotation automation                             | [PLANNED — post-cutover] |
| Automated secret scanning (git history)                | [PLANNED — post-cutover] |
| Secret access audit logging                            | [PLANNED — post-cutover] |
| Rotation notification workflow                         | [PLANNED — post-cutover] |
