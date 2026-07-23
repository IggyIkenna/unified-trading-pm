---
doc_type: codex-ssot
title: Secret Naming Convention
summary: >-
  SUPERSEDED 2026-07-23 — merged into codex/05-infrastructure/secret-manager-naming.md (§ 1.1), which had the same
  authoritative_for claim (a retrieval-layer collision this merge resolves). Content retained below for history.
status: superseded
superseded_by: ../05-infrastructure/secret-manager-naming.md
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: [secrets, execution, cefi, ssot-audit]
related: [secrets-management.md, client-credentials.md, ../05-infrastructure/secret-manager-naming.md]
created: 2026-03-27
authoritative_for:
referenced_by:
  [
    codex/04-architecture/data-tranches.md,
    codex/07-security/client-credentials.md,
    codex/07-security/secrets-management.md,
    codex/07-security/service-to-service-auth.md,
  ]
owner:
last_reviewed: 2026-07-23
code_refs:
---

# Secret Naming Convention

> # ⛔ SUPERSEDED 2026-07-23 (doc-reconciliation, operator-approved "merge both")
>
> **Live SSOT: [`../05-infrastructure/secret-manager-naming.md`](../05-infrastructure/secret-manager-naming.md) § 1.1.**
> This doc and that one both carried `authoritative_for: [Secret Manager naming convention]` verbatim — an agent
> grepping that topic got a coin flip.
>
> **The pattern below, `exec-{client}-{venue}-{account_type}`, was itself wrong** — no secret with that shape exists. A
> follow-up pass queried the live GCP Secret Manager inventory directly (194 secrets, project `central-element-323112`)
> and found the real, already-provisioned pattern is `exec-{client}-{venue}-{field}` (field = `api-key` / `api-secret` /
> `passphrase`-for-OKX-only) — confirmed live for OKX (8 clients) and Binance (2 clients). `CredentialsRegistry` (in
> `unified_trading_library.cloud_interface`, **not** the `unified_cloud_interface` package this doc cites — that repo
> isn't checked out anywhere in this workspace) has been corrected to match. The merged doc's § 1 also resolves the
> read/trade-split question this doc didn't address: Binance/Deribit split read/trade/write, Bybit/Aster use one
> unscoped key, Hyperliquid is wallet-style. Everything below is retained for history only — do not treat any secret
> name in this file as current.

**SSOT:** This document is the canonical reference for Secret Manager naming in the Unified Trading System. All new
secrets MUST follow these patterns before being provisioned.

The `CredentialsRegistry` class in `unified_cloud_interface.credentials_registry` enforces these patterns
programmatically — any venue or service credential lookup routes through that registry.

---

## Pattern Matrix

| Category                            | Pattern                                | Example                             |
| ----------------------------------- | -------------------------------------- | ----------------------------------- |
| Venue execution keys (per-client)   | `exec-{client}-{venue}-{account_type}` | `exec-odum-binance-cefi`            |
| Venue API credentials (system-wide) | `{venue}-api-credentials`              | `binance-api-credentials`           |
| Venue read keys (split key/secret)  | `{venue}-read-api-key`                 | `deribit-read-api-key`              |
| Venue trade keys (split key/secret) | `{venue}-trade-api-key`                | `binance-trade-api-key`             |
| Service accounts                    | `{service}-service-account`            | `execution-service-service-account` |
| Infrastructure secrets              | `{env}-{resource}-{type}`              | `prod-redis-password`               |
| Data vendor keys                    | `{vendor}-api-key`                     | `tardis-api-key`                    |
| Sports / prediction markets         | `{venue}-api-credentials`              | `betfair-api-credentials`           |

---

## Rules

| Rule                                    | Rationale                                                       |
| --------------------------------------- | --------------------------------------------------------------- |
| Lowercase, hyphen-separated only        | Consistent discovery; no `bybit_api_key` (underscore violation) |
| No version numbers in names             | Use Secret Manager versioning, not name suffixes                |
| No `change-me` placeholder values       | Caught by quality gate; must fail loud if secret absent         |
| Client prefix for client-scoped secrets | `exec-{client}-*` makes IAM scoping explicit                    |
| Venue name matches canonical venue ID   | `binance`, `deribit`, `okx` — not `Binance`, `DERIBIT`, `OKX`   |
| Credential type is last segment         | `-api-key`, `-api-secret`, `-passphrase`, `-credentials`        |

---

## Execution Key Pattern: `exec-{client}-{venue}-{account_type}`

Used by `execution-service` to look up per-client exchange credentials. The three-tranche data wiring in
`tranche_router.py` resolves to this pattern for Tranche B (Secret Manager live execution).

```python
from unified_cloud_interface import CredentialsRegistry, get_secret_client

secret_name = CredentialsRegistry.exec_secret_for_client("odum", "binance", "cefi")
# -> "exec-odum-binance-cefi"

creds_json = get_secret_client().access_secret(secret_name)
```

### Account type values

| Value    | Meaning                                               |
| -------- | ----------------------------------------------------- |
| `cefi`   | CeFi exchange account (Binance, Deribit, OKX, Bybit)  |
| `defi`   | DeFi / onchain execution (Hyperliquid EIP-712 wallet) |
| `tradfi` | TradFi brokerage (IBKR paper/live)                    |
| `sports` | Sports betting exchange (Betfair, Pinnacle)           |

---

## Service Account Pattern: `{service}-service-account`

GCP service accounts used for inter-service IAM auth. Each service has one service account secret containing the JSON
key. The `CredentialsRegistry.service_account_secret()` method returns the canonical name.

```python
sa_secret = CredentialsRegistry.service_account_secret("execution-service")
# -> "execution-service-service-account"
```

---

## Infrastructure Secrets Pattern: `{env}-{resource}-{type}`

| Secret                   | Purpose                             |
| ------------------------ | ----------------------------------- |
| `prod-redis-password`    | Redis cluster password (production) |
| `staging-redis-password` | Redis cluster password (staging)    |
| `prod-postgres-password` | PostgreSQL instance password        |

---

## Data Vendor Pattern: `{vendor}-api-key`

| Secret              | Vendor                          |
| ------------------- | ------------------------------- |
| `tardis-api-key`    | Tardis.dev historical tick data |
| `databento-api-key` | Databento market data           |
| `fred-api-key`      | FRED macroeconomic data         |
| `thegraph-api-key`  | The Graph subgraph queries      |
| `alchemy-api-key`   | Alchemy Ethereum RPC            |

---

## Known Violations (to fix)

| Current Name       | Canonical Name             | Status                                                          |
| ------------------ | -------------------------- | --------------------------------------------------------------- |
| `bybit_api_key`    | `bybit-api-key`            | Must rename — underscore not allowed                            |
| `bybit_api_secret` | `bybit-api-secret`         | Must rename — underscore not allowed                            |
| `betfair_app_key`  | `betfair-api-credentials`  | Must rename — underscores not allowed; consolidate to JSON blob |
| `ibkr-tws-key`     | `ibkr-account-credentials` | Rename for consistency with VENUE_SECRET_MAP                    |
| `graph-api-key`    | `thegraph-api-key`         | Deprecated alias — delete after all consumers migrated          |

---

## Enforcement

- `CredentialsRegistry` in UCI raises `KeyError` for unregistered venues/services
- Quality gate (`quality-gates.sh`) rejects any `os.getenv()` for secret values
- `.cursorrules` prohibits hardcoded API key strings in source code
- `get_secret_client()` is the only approved secret access path (no `os.getenv` fallback)

## Cross-references

- `unified-trading-pm/codex/07-security/secrets-management.md` — full secret inventory + provisioning status
- `unified-cloud-interface/unified_cloud_interface/credentials_registry.py` — programmatic SSOT
- `unified-trading-pm/credentials-registry.yaml` — operational credentials registry (cost, required_for, status)
