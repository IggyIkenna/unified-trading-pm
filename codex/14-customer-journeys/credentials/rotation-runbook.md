---
scope: [admin, engineer]
last_reviewed: 2026-05-17
execution:
  owner: "operator (ikenna) — per-source credential rotation"
  cadence: "per-source (see body table — typically 90d)"
  verifier: "gcloud secrets versions list --secret=<source>_api_key + verify latest enabled within cadence"
  last_executed: "per-source rotation log appended in body; cross-ref codex/05-infrastructure/rotation-runbook.md"
---

# Per-source credential rotation runbook — sports, prediction, DeFi data

> **Created 2026-05-15** per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 5.A.2. Full cross-class rotation cadence is at
> [`codex/05-infrastructure/rotation-runbook.md`](../../05-infrastructure/rotation-runbook.md).
>
> This doc specialises on **data-source** credentials (sports, prediction, DeFi data) per the Runbook
> Execution-Owner SSOT HARD RULE (4 required fields: `owner` / `cadence` / `verifier` / `last_executed`).

---

## § 1 — Sports data sources (90d cadence)

### 1.1 api-football (apifootball.com)

```yaml
execution:
  owner: operator (ikenna@odum-research.com)
  cadence: 90d
  verifier: credential-probe.sh --mode live --archetype carry_staked_basis returns api_football PASS
  last_executed: NEVER
```

Secret Manager name: `prod-instruments-service-api-football-key` (see
[`secret-manager-naming.md`](../../05-infrastructure/secret-manager-naming.md)).

Steps:

1. Log in to apifootball.com dashboard → API Keys → Regenerate.
2. `gcloud secrets versions add prod-instruments-service-api-football-key --data-file=- <<< "$NEW_KEY"`.
3. Wait ≤5 min for `ApiKeyReloader` cycle; verify via `curl ${instruments_svc}/health/credentials | jq '.api_football'`.
4. Revoke old key in apifootball.com dashboard.

### 1.2 footystats (footystats.org)

```yaml
execution:
  owner: operator (ikenna@odum-research.com)
  cadence: 90d
  verifier: credential-probe.sh returns footystats PASS
  last_executed: NEVER
```

Secret Manager name: `prod-instruments-service-footystats-key`.

Same rotation steps as 1.1 (substitute dashboard + secret name).

### 1.3 soccer-football-info (sfi)

```yaml
execution:
  owner: operator (ikenna@odum-research.com)
  cadence: 90d
  verifier: credential-probe.sh returns sfi PASS
  last_executed: NEVER
```

Secret Manager name: `prod-instruments-service-sfi-key`.

### 1.4 Public sources — NO ROTATION (excluded)

The following sports data sources are **public / key-free** — excluded from rotation tracking per
[`deployment-service@9943e7c9`](../../../deployment-service) Phase 5.A.3 comment:

- **understat** — public football stats, no API key
- **transfermarkt** — public player valuation scrape, no API key
- **open_meteo** — public weather API, no API key
- **pyth-hermes** — Pyth Network price feeds are on-chain public; Pyth-Hermes HTTP relay has no authentication

These sources are NOT in `_TRADE_KEY_PATTERNS` / `_DATA_KEY_PATTERNS` in `deployment-service/scripts/audit/credential-probe.sh`.

---

## § 2 — Prediction venue credentials (60d cadence)

### 2.1 Polymarket

```yaml
execution:
  owner: operator (ikenna@odum-research.com)
  cadence: 60d
  verifier: credential-probe.sh returns polymarket_api_key PASS
  last_executed: NEVER
```

Secret Manager name: `prod-execution-service-polymarket-api-key` (added to `_TRADE_KEY_PATTERNS` 2026-05-09;
secret value provisioning: BLOCKED-OPERATOR per Phase 5.B.1).

### 2.2 Kalshi

```yaml
execution:
  owner: operator (ikenna@odum-research.com)
  cadence: 60d
  verifier: credential-probe.sh returns kalshi_api_key PASS
  last_executed: NEVER
```

Secret Manager name: `prod-execution-service-kalshi-api-key` (verify provisioned per Phase 5.B.2).

---

## § 3 — DeFi data credentials (90d cadence)

### 3.1 Helius (Solana RPC + NFT / DAS API)

```yaml
execution:
  owner: operator (ikenna@odum-research.com)
  cadence: 90d
  verifier: credential-probe.sh returns helius_api_key PASS
  last_executed: NEVER
```

Secret Manager name: `prod-execution-service-helius-api-key` (added to `_DATA_KEY_PATTERNS` 2026-05-09).

### 3.2 CoinGecko

```yaml
execution:
  owner: operator (ikenna@odum-research.com)
  cadence: 90d
  verifier: credential-probe.sh returns coingecko_api_key PASS
  last_executed: NEVER
```

Secret Manager name: `prod-instruments-service-coingecko-key` (added to `_DATA_KEY_PATTERNS` 2026-05-09).

### 3.3 Tenderly (fork + simulation)

```yaml
execution:
  owner: operator (ikenna@odum-research.com)
  cadence: 90d
  verifier: credential-probe.sh returns tenderly_access_key PASS
  last_executed: NEVER
```

Secret Manager name: `prod-execution-service-tenderly-access-key`.

---

## § 4 — References

- [`codex/05-infrastructure/rotation-runbook.md`](../../05-infrastructure/rotation-runbook.md) — cross-class cadence
  (wallets, CMK, CeFi trade-scope, withdraw-scope, aux).
- [`codex/05-infrastructure/credentials-matrix.md`](../../05-infrastructure/credentials-matrix.md) — workspace
  credential SSOT (full enumeration).
- [`codex/05-infrastructure/secret-manager-naming.md`](../../05-infrastructure/secret-manager-naming.md) — secret name
  conventions.
- [`deployment-service/scripts/audit/credential-probe.sh`](../../../deployment-service/scripts/audit/credential-probe.sh) —
  automated probe + verification.
