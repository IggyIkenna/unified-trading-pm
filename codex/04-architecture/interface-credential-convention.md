---
scope: [engineer, admin]
---

# Interface Credential Convention

## Principle

Interfaces are API-keyless. They define connectivity and protocol logic only. Services fetch credentials from Secret
Manager and inject them at runtime via factory/constructor parameters.

## The Convention

### 1. Active Repos with Execution/Data Adapters (UMI, execution-service, instruments-service, position-balance-monitor-service, UFI, UEI, UCI)

NOTE: UTEI (unified-trade-execution-interface), UDEI (unified-defi-execution-interface), USEI
(unified-sports-execution-interface) have been merged into **execution-service**. URDI
(unified-reference-data-interface) merged into **instruments-service**. UPI (unified-position-interface) merged into
**position-balance-monitor-service**. Additionally: UMLi (unified-ml-interface) merged into **unified-trading-library**
(ml/ sub-package). UDC (unified-domain-client) merged into **unified-trading-library** (domain_client/ sub-package).
USRI (unified-sports-reference-interface) merged into **unified-reference-data-interface** (sports/ sub-package).
unified-feature-orchestration-library merged into **unified-trading-library** (feature_service_base/ sub-package).
unified-trading-library merged into **unified-trading-library** (feature_calculator/ sub-package).
execution-algo-library merged into **execution-service** (algo_library/ sub-package). matching-engine-library merged
into **execution-service** (matching_engine/ sub-package).

- Accept credentials as constructor/factory parameters
- Never call `get_secret_client()` internally
- Never read from environment variables for API keys
- Define protocol logic, serialization, and connectivity only

### 2. Services (instruments-service, market-tick-data-service, execution-service, etc.)

- Fetch credentials from Secret Manager using UCI `get_secret_client()`
- Pass resolved values to interface factories/constructors
- Manage credential lifecycle (rotation, per-environment differences)
- Handle dev/staging/prod IAM boundaries

### 3. UAC (unified-api-contracts)

- Holds static mappings: base URLs, testnet URLs, chain configs, RPC URL templates
- `capability_declarations` define what each venue supports (operations, environments, auth types)
- No credentials -- only connectivity metadata

### 4. UCI (unified-cloud-interface)

- `CredentialsRegistry`: SSOT for secret names (string constants only)
- Provides `get_secret_client()` for services to use
- Does NOT fetch secrets on behalf of interfaces

## Pattern by Repo/Adapter

| Repo/Adapter               | Factory Signature                                                      | What Services Pass                         |
| -------------------------- | ---------------------------------------------------------------------- | ------------------------------------------ |
| execution-service (CeFi)   | `get_order_adapter(venue, api_key, api_secret, ...)`                   | Exchange API key + secret                  |
| execution-service (DeFi)   | `connector.connect(config={"wallet_private_key": pk, "rpc_url": url})` | Wallet key + resolved RPC URL              |
| execution-service (Sports) | `adapter(credentials={"api_key": key, ...})`                           | Venue-specific credentials                 |
| execution-service (Custody) | `get_custody_provider(CustodyConfig(provider, ...))`                   | Per-`signing_surface` config (see § Custody) |
| instruments-service        | `create_adapter(venue, api_key=key)`                                   | Data provider API key                      |
| UMI                        | `get_adapter(venue)`                                                   | None (public endpoints)                    |
| UEI                        | `setup_events()`                                                       | None (ADC for PubSub)                      |
| UFI                        | N/A                                                                    | None (public APIs)                         |
| UCI                        | N/A                                                                    | Provides `get_secret_client()` to services |

### Custody (per-wallet signing surface — added 2026-05-12 by Phase 3.C SPLIT)

Per [`custody-providers.md`](custody-providers.md) § 1, custody signing routes
through a single factory `get_custody_provider(config: CustodyConfig)` that
picks the right `CustodyProvider` implementation per `config.provider`. The
provider name comes from UAC `WalletProvisioningConfig.signing_surface` (per
[`per-archetype-wallet-isolation.md`](../05-infrastructure/per-archetype-wallet-isolation.md)
§ 6 + UAC@`d721b6a` schema):

| `signing_surface`         | `config.provider` | Required `CustodyConfig` fields                     | Notes |
|---------------------------|--------------------|------------------------------------------------------|-------|
| `LOCAL_KEY`               | `local_key`        | `private_key` (raw PK), `rpc_url`                    | Dev / testnet only |
| `CLOUD_KMS_ENCRYPTED`     | `cloud_kms`        | `kms_key_uri`, `private_key_secret_ref`, `rpc_url`   | **May-23 cutover default** (per R9 RESOLVED 2026-05-12) — shipped at execution-service@`d45d24b4` |
| `COPPER_MPC`              | `copper`           | `api_key`, `api_secret`, `organization_id`           | June-1 client-cred flip target |
| `FIREBLOCKS_MPC`          | `fireblocks`       | `api_key`, `api_secret`, `vault_account_id` (via `organization_id`) | June-1 client-cred flip target (Phase 3.C.2 deferred-after-cutover) |
| `MOCK`                    | `mock`             | None                                                 | Test-only |

**Per-wallet flippability**: each `WalletProvisioningConfig` row carries its
own `signing_surface` — operator flips the field in
`gs://wallet-config-{pid}/{chain_env}/wallet_provisioning.json` + service
reloads via `ApiKeyReloader` — **no recompile, no service restart**.

## Why This Convention

- **Testability**: Interfaces can be tested without real credentials -- pass mocks/stubs
- **IAM boundaries**: Different service accounts per environment (dev/staging/prod) with different SM access
- **Credential rotation**: Services manage rotation centrally, interfaces don't cache stale keys
- **Separation of concerns**: Protocol logic (interface) vs operational security (service)

## Anti-Patterns

- Interface calling `get_secret_client()` directly
- Interface reading API keys from environment variables
- Interface with `CredentialsRegistry` import for fetching (constants-only import is OK)
- Service passing `project_id` for interface to resolve keys internally
