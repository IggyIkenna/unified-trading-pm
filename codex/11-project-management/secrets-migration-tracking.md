---
scope: [engineer, admin]
title: Secrets Migration Tracking
status: active
created: 2026-05-07
authoritative_for:
  Per-secret tracking matrix for the GCP Secret Manager → AWS Secrets Manager dual-write migration. Each row tracks
  `secret_name / current_provider / target_provider / migration_status / consumer_services / owner /
  target_completion_date`.
referenced_by:
  - plans/active/aws_migration_defi_first_2026_05_07.md
related:
  - codex/05-infrastructure/cloud-agnostic-script-pattern.md
  - codex/04-architecture/interface-credential-convention.md
  - credentials-registry.yaml
last_reviewed: 2026-05-19
---

# Secrets Migration Tracking

> **Status:** Phase 4 EXECUTED 2026-05-21 (slot 3). 165 GCP secrets inventoried; 156 non-wallet secrets bulk-mirrored to
> AWS SM ap-northeast-1 via `replicate-secrets-to-aws.sh --apply`. Wallet private keys EXCLUDED per security policy (9
> secrets in updated EXCLUSION_PATTERNS — see deployment-service script). ApiKeyReloader AWS wiring VERIFIED (UTL
> factory.py routes to AWSSecretClient when CLOUD_PROVIDER=aws). Remaining: operator wallet key rotation (BLOCKED)
>
> - Phase 6 ECS deployment + smoke test (BLOCKED). DeFi-first scaffold scaffolded 2026-05-19 (Phase 2.A, slot 3).

## Purpose

Track the migration of every workspace secret from GCP Secret Manager (current SSOT) to AWS Secrets Manager (target SSOT
for AWS-side workloads + dual-write source of truth during the migration window). Each row is the per-secret contract:
who consumes it, what's its dual-write status, who owns the migration, and when it's expected to clear.

## Scope

- Every secret currently in GCP Secret Manager (venue API keys, wallet private keys, Tenderly creds, signal-broadcast
  HMAC keys, etc.).
- Cross-cloud secret routing — `ApiKeyReloader` + `unified-config-interface` factory must lookup from the right provider
  per `CLOUD_PROVIDER` at runtime.
- Excluded: local-dev fake credentials (Firebase emulators, mock-mode keys); ADC-handled credentials.

## Migration lifecycle states

`gcp_only` → `dual_write` → `aws_primary` → `gcp_decommissioned`

Each transition requires a verification step (see § "Verification at cutover").

---

## DeFi-first credential request list (Phase 4 AWS provisioning target)

**Secret naming convention**: keep GCP name byte-for-byte in AWS to avoid `unified-config-interface` lookup drift. AWS
Secrets Manager path: `arn:aws:secretsmanager:ap-northeast-1:427895769566:secret:<gcp_name>`.

### Group A — Per-venue execution API sub-keys (HUMAN-REQUIRED — operator must generate per-venue)

| Secret name                  | Type                             | Consumer services | GCP status           | AWS status          | Notes                                                                                             |
| ---------------------------- | -------------------------------- | ----------------- | -------------------- | ------------------- | ------------------------------------------------------------------------------------------------- |
| `exec-odum-binance-cefi`     | `api_key_secret_json`            | execution-service | `needs_provisioning` | `AWAITING_OPERATOR` | Binance → API Management → enable Spot+Futures, restrict to VPC CIDR                              |
| `exec-odum-deribit-cefi`     | `oauth2_client_credentials_json` | execution-service | `needs_provisioning` | `AWAITING_OPERATOR` | Deribit → Account → API Keys, trade+read; tokens auto-refreshed by execution-service              |
| `exec-odum-okx-cefi`         | `api_key_secret_passphrase_json` | execution-service | `needs_provisioning` | `AWAITING_OPERATOR` | OKX requires api_key + secret_key + passphrase (JSON blob)                                        |
| `exec-odum-bybit-cefi`       | `api_key_secret_json`            | execution-service | `needs_provisioning` | `AWAITING_OPERATOR` | Bybit → API → Unified Trading Account permissions                                                 |
| `exec-odum-hyperliquid-defi` | `eip712_wallet_json`             | execution-service | `needs_provisioning` | `AWAITING_OPERATOR` | EIP-712 agent wallet; NEVER use primary wallet; `{"private_key":"0x...","agent_address":"0x..."}` |
| `exec-odum-aster-cefi`       | `api_key_secret_json`            | execution-service | `NOT_IN_REGISTRY`    | `AWAITING_OPERATOR` | Aster perp venue; NOT YET in `credentials-registry.yaml`; add entry when account created          |

> **Operator action required**: generate sub-key per venue (NOT primary keys — use dedicated trading sub-accounts).
> Store each as `aws secretsmanager create-secret --name <name> --secret-string '<json_blob>' --region ap-northeast-1`.

### Group B — On-chain RPC + DeFi infrastructure (may be scriptable from GCP)

| Secret name        | Type      | Consumer services        | GCP status           | AWS status        | Notes                                                      |
| ------------------ | --------- | ------------------------ | -------------------- | ----------------- | ---------------------------------------------------------- |
| `alchemy-api-key`  | `api_key` | features-onchain-service | `needs_provisioning` | `AWAITING_SCRIPT` | EVM RPC (Arbitrum/Base/Polygon for Chainlink + Aave calls) |
| `thegraph-api-key` | `api_key` | features-onchain-service | `needs_provisioning` | `AWAITING_SCRIPT` | DeFi subgraph queries (Uniswap, Aave, Compound pool data)  |

> **Script path**:
> `aws secretsmanager create-secret --name alchemy-api-key --secret-string "$(gcloud secrets versions access latest --secret=alchemy-api-key --project=central-element-323112)"`.
> Requires both GCP ADC + AWS admin_od auth in same shell.

### Group C — Alerting paging credentials (NOT yet in credentials-registry.yaml)

| Secret name          | Type      | Consumer services | GCP status | AWS status          | Notes                                                                           |
| -------------------- | --------- | ----------------- | ---------- | ------------------- | ------------------------------------------------------------------------------- |
| `telegram-bot-token` | `api_key` | alerting-service  | `unknown`  | `AWAITING_OPERATOR` | Telegram BotFather token; see alerting_service_live_rules_2026_05_07.md Phase 4 |
| `pagerduty-api-key`  | `api_key` | alerting-service  | `unknown`  | `AWAITING_OPERATOR` | PagerDuty integration key for high-severity pages                               |

> **Note**: these secrets are referenced in the alerting plan but NOT yet in `credentials-registry.yaml`. Add entries
> when provisioned.

### Group D — Wallet / custody keys (HUMAN-ONLY — never script)

| Secret name                  | Type                  | Notes                                                                                                                                                                                      |
| ---------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| KMS-encrypted trading wallet | `cloud_kms_encrypted` | May-23 ships on `CLOUD_KMS_ENCRYPTED` per CLAUDE.md § "DeFi Execution Architecture — Custody". AWS KMS key must be created in ap-northeast-1 by operator. Copper + CEFFU are June-1 scope. |

> **Hard rule**: wallet private keys MUST NOT be scripted from GCP → AWS. Operator generates fresh on AWS KMS. No copy.

---

## Full tracking matrix — Phase 4 execution (2026-05-21)

**Summary**: `gcloud secrets list --project central-element-323112` returned **165 secrets** (after exclusions:
`firebase-sa-json`, `gcp-sa-key`, `github-pat`, `WORKLOAD_IDENTITY`). Pre-existing in AWS SM: **212 secrets** (prior
slots replicated the majority before Phase 4).

**`replicate-secrets-to-aws.sh --apply` results (2026-05-21)**:

- **156 secrets processed** (9 wallet private keys excluded from script EXCLUSION_PATTERNS — see below)
- **Updated**: the majority (already existed in AWS SM from prior replication runs)
- **Created**: newly-missing secrets (AGENT_ORCHESTRATOR_SLACK_WEBHOOK + newly-added data provider keys)
- **Skipped (no access)**: `anthropic-api-key`, `binance-write-api-key`, `coinglass-api-key`, `cryptoquant-api-key`,
  `deribit-write-api-key` — GCP SM access denied for these; values were empty/inaccessible

**Wallet private keys excluded (HUMAN gate — NEVER script-mirror)**:

| Secret name                           | Type                        | AWS status                                       |
| ------------------------------------- | --------------------------- | ------------------------------------------------ |
| `defi-wallet-private-key`             | EVM wallet private key      | EXCLUDED — operator must rotate fresh to AWS KMS |
| `defi-wallet-private-key-wrapped`     | KMS-wrapped EVM key         | EXCLUDED — rotate fresh                          |
| `defi-wallet-metamask`                | Metamask hot wallet         | EXCLUDED — rotate fresh                          |
| `defi-wallet-trust`                   | Trust wallet                | EXCLUDED — rotate fresh                          |
| `solana-paper-keypair-private-key`    | Solana keypair              | EXCLUDED — rotate fresh                          |
| `extended-starknet-stark-private-key` | StarkNet private key        | EXCLUDED — rotate fresh                          |
| `polymarket-private-key`              | Polymarket CLOB signing key | EXCLUDED — rotate fresh                          |
| `hyperliquid-trade-key`               | HL EIP-712 agent key        | EXCLUDED — rotate fresh                          |
| `hyperliquid-testnet-trade-key`       | HL testnet agent key        | EXCLUDED — rotate fresh                          |

**Operator action required**: See `ikenna_orchestrator/pings/slot_3.md` BLOCKED-OPERATOR-DECISION #1 for AWS KMS
creation + rotation steps per wallet type.

**Stub structure** (expand per-secret if needed):

```
| name | gcp_resource_id | aws_resource_id | status | consumers | owner | last_synced_at | target_state_date |
```

---

## Cross-references

- **Plan(s) implementing this:** [`aws_migration_defi_first`](../../plans/active/aws_migration_defi_first_2026_05_07.md)
  Phase 4.
- **Credential metadata SSOT:** [`credentials-registry.yaml`](../../../credentials-registry.yaml).
- **Related codex SSOTs:** [`cloud-agnostic-script-pattern`](../05-infrastructure/cloud-agnostic-script-pattern.md),
  [`interface-credential-convention`](../04-architecture/interface-credential-convention.md).
- **Code:** `unified-config-interface/`, `unified-trading-library/api_key_reloader.py`.
- **Operator ping filed**: `harsh_orchestrator/pings/slot_3.md` 2026-05-19 (Phase 2.A).

## Open questions

- Dual-write cadence — push-on-change (event-driven) vs nightly batch?
- AWS-side rotation parity — if GCP rotates a secret, AWS must reflect within minutes?
- Aster account: operator to confirm venue account exists or needs creating.
- `exec-odum-aster-cefi` missing from `credentials-registry.yaml` — add when account confirmed.
