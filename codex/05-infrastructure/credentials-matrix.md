---
scope: [engineer, admin]
---

# Credentials matrix — workspace SSOT

> **Created 2026-05-12** by slot 4 per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 9.A. Closes out 6 stub codex docs declared in Phase 0.D.

This is the workspace SSOT for **every credential** the system uses across
all modes (paper / batch / live) and all surfaces (cloud / venue / custody /
data / aux). Reader: `credential-probe.sh` audit script + per-service
health endpoints + operator runbook.

---

## § 1 — Credential classes

| Class | Examples | Storage | Rotation cadence |
|---|---|---|---|
| **Cloud infra** | GCP service accounts, AWS IAM roles, Cloud HSM CMKs, KMS keys | GCP IAM + AWS IAM + Secret Manager | per-CMK 90d (auto); IAM roles indefinite |
| **Custody** | Copper API key + secret + org-id, CEFFU equivalents, Fireblocks API key + RSA PEM, wallet PKs (envelope-encrypted) | GCP Secret Manager (`<service>-api-key` paths) | 60d for HMAC creds; quarterly for Fireblocks RSA |
| **Venue trade** | Per-venue per-scope `<venue>-{read,trade,withdraw}-{api-key,api-secret,passphrase}` for 10 venues × 3 scopes | GCP Secret Manager | 30d trade-scope; 60d read-scope |
| **Venue prediction** | polymarket / kalshi / manifold | GCP Secret Manager | 60d |
| **Data sources** | api-football / footystats / soccer-football-info / helius / coingecko / tenderly-access-key / barchart / yahoo | GCP Secret Manager | 90d (data only — lower risk) |
| **Aux services** | telegram-bot-token-{dev,staging,prod} / firebase-sa-json / anthropic-api-key | GCP Secret Manager | 90d |
| **GHA WIF** | GCP/AWS → GitHub OIDC trust pool | GCP Workload Identity Federation + AWS STS trust policy | indefinite (no long-lived PAT) |

---

## § 2 — Per-mode credential subsets

SSOT YAML: [`unified-api-contracts/config/credentials_per_mode.yaml`](../../unified-api-contracts/config/credentials_per_mode.yaml).

| Mode | Custody | Venue | Data | Aux |
|---|---|---|---|---|
| `paper` | sandbox + mock | (none — fork fills) | live read-only | dev telegram |
| `batch` | mock | read-scope only | live (historical sources) | dev telegram |
| `live` | CLOUD_KMS (May-23) → COPPER/FIREBLOCKS (June-1) | trade-scope (full) | live | prod telegram |

---

## § 3 — Per-archetype credential subsets

SSOT YAML: [`unified-api-contracts/config/credentials_per_archetype.yaml`](../../unified-api-contracts/config/credentials_per_archetype.yaml).

Cutover archetypes:
- `carry_staked_basis` — 5 wallet wrapped PKs + 6 perp hedge venues + cloud_kms_cmk_defi + helius + coingecko + telegram.
- `ARBITRAGE_PRICE_DISPERSION` (config variants: funding_rate_dispersion + cross_venue_price_dispersion) — same wallet shape + relevant venue keys.

---

## § 4 — Per-cloud parity

GCP Secret Manager (prod project `central-element-323112`) is canonical;
AWS Secrets Manager (`ap-northeast-1` account `427895769566`) mirrors per
Plan Phase 1.E. Cross-cloud abstraction via `UnifiedCloudConfig` — service
code never branches on cloud.

```python
config = UnifiedCloudConfig(provider="gcp")  # or "aws"
value = config.get_secret("copper-api-key")  # round-trips on both
```

---

## § 5 — Naming convention

SSOT: [`secret-manager-naming.md`](secret-manager-naming.md).

Pattern: `<class>-<surface>-<role>-<version>` (per § 2 of naming SSOT).

---

## § 6 — Continuous verification

Every credential class declares cadence + execution-owner per
`Runbook Execution-Owner SSOT` HARD RULE:

```yaml
execution:
  owner: deployment-service maintainer + ikennaigboaka (operator)
  cadence: daily cron VM `credential-probe-vm`
  verifier: credential-probe.sh --mode live returns 100% pass
  last_executed: NEVER
```

Pre-cutover gate (2026-05-22): full probe MUST return 100% pass before
live-trading kill-switch disarms.

---

## § 7 — References

- [`secret-manager-naming.md`](secret-manager-naming.md) — naming SSOT.
- [`custody-onboarding-checklist.md`](custody-onboarding-checklist.md) — operator runbook.
- [`fireblocks-integration-spec.md`](fireblocks-integration-spec.md) — June-1 paste-ready spec.
- [`per-archetype-wallet-isolation.md`](per-archetype-wallet-isolation.md) — multi-wallet model.
- [`hsm-wallet-signing.md`](hsm-wallet-signing.md) — HSM tier discipline.
- [`aws-iam-matrix.md`](aws-iam-matrix.md) — per-service AWS IAM SSOT (PENDING Phase 1.B).
