---
doc_type: codex-ssot
title: Per-Client Exchange Credentials
summary:
  Per-client exchange credentials stored in Secret Manager as `{client}-{venue}-{credential-type}` (`-api-key` /
  `-api-secret` / `-passphrase`), accessed at runtime via `get_secret_client()`; consumed by execution-service.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [secrets, execution, cefi, credentials]
related: [/codex/07-security/secrets-management.md, /codex/07-security/secret-naming-convention.md]
created: 2026-03-27
authoritative_for: [per-client exchange credential secrets]
referenced_by: [/codex/07-security/secret-naming-convention.md, /codex/07-security/secrets-management.md]
owner:
last_reviewed:
code_refs:
---

# Per-Client Exchange Credentials

Exchange API credentials are stored per client and per venue in GCP Secret Manager (or AWS Secrets Manager when
`CLOUD_PROVIDER=aws`).

## Secret Naming Pattern

```
{client}-{venue}-{credential-type}
```

| Credential Type | Purpose             | Required By                               |
| --------------- | ------------------- | ----------------------------------------- |
| `-api-key`      | Exchange API key    | All venues                                |
| `-api-secret`   | Exchange API secret | Most venues (Binance, Deribit, OKX, etc.) |
| `-passphrase`   | Exchange passphrase | Some venues (e.g. Coinbase, KuCoin)       |

## Examples

| Secret Name                       | Used For                         |
| --------------------------------- | -------------------------------- |
| `client-alpha-binance-api-key`    | Binance API key for client-alpha |
| `client-alpha-binance-api-secret` | Binance API secret               |
| `client-alpha-deribit-api-key`    | Deribit API key                  |
| `client-alpha-deribit-api-secret` | Deribit API secret               |
| `client-alpha-kucoin-api-key`     | KuCoin API key                   |
| `client-alpha-kucoin-api-secret`  | KuCoin API secret                |
| `client-alpha-kucoin-passphrase`  | KuCoin passphrase / API key note |

## Access Pattern

Credentials are accessed at runtime via `get_secret_client()` from `unified_cloud_interface`:

```python
from unified_cloud_interface import get_secret_client

secret_client = get_secret_client()
api_key = secret_client.access_secret("client-alpha-binance-api-key")
api_secret = secret_client.access_secret("client-alpha-binance-api-secret")
```

## Used By

- **execution-service** — fetches credentials when placing orders on behalf of a client at a venue.

## Rules

- Venue name must match canonical venue ID (lowercase: `binance`, `deribit`, `okx`).
- Client identifier must match the client's canonical ID in the system.
- Never commit credentials; all values live in Secret Manager.
- See [secrets-management.md](./secrets-management.md) for the full secret access pattern.
