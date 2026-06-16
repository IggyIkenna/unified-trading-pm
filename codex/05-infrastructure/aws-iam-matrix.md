---
scope: [admin, engineer]
last_reviewed: 2026-05-17
---

# AWS IAM matrix — per-service role + policy SSOT

> **Created 2026-05-12** by slot 4 per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 9.B (PENDING Phase 1.B operator provisioning — stub provides per-service shape + closed-set policy attachments
> for slot-4-successor / Harsh to apply via Terraform / CDK).

**Status**: 🟡 **SHAPE-ONLY STUB** — provider exists, IAM resources NOT yet provisioned. Acceptance gate per Plan Phase
1.B § verification: `aws iam list-roles --query 'Roles[?starts_with(RoleName, \`uts-\`)].RoleName'` returns 19+ entries
(one per service).

---

## § 1 — Naming convention

```
uts-{service-short-name}-{env}
```

- `service-short-name` ∈ closed set: `instruments` / `mtds` / `mdps` / `features` / `strategy` / `execution` / `pbms` /
  `risk` / `alerting` / `signal-broadcast` / `deployment` / `client-reporting` / `trade-event` /
  `unified-trading-system-ui` / `batch-live-recon` / `disaster-recovery` / `oracle-aggregation` / `feature-onchain` /
  `feature-sports`.
- `env` ∈ `prod` / `staging` / `dev` (mirrors GCP service-account `env` suffix).

Example: `uts-execution-prod`, `uts-mtds-staging`, `uts-deployment-dev`.

---

## § 2 — Per-service IAM matrix (target shape)

| Service                   | S3 access                                                                                      | Secrets Manager                                                                                | KMS                                                                           | SNS/SQS                                                            | EventBridge                     | EC2                                                                  | ECS                              |
| ------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------- | -------------------------------------------------------------------- | -------------------------------- |
| instruments               | `unified-trading-instruments-{env}` (R/W) + `unified-trading-instrument-manifests-{env}` (R/W) | per-service venue read keys                                                                    | —                                                                             | publish `instruments-events`                                       | trigger nightly catalog refresh | —                                                                    | —                                |
| mtds                      | `unified-trading-market-data-{env}` (R/W) + `unified-trading-instrument-manifests-{env}` (R)   | per-venue read + websocket keys                                                                | —                                                                             | publish `market-tick-events`                                       | trigger forward-poll cron       | —                                                                    | —                                |
| mdps                      | `unified-trading-market-data-{env}` (R/W) + `unified-trading-market-data-derived-{env}` (R/W)  | none                                                                                           | —                                                                             | subscribe `market-tick-events` + publish `market-derived-events`   | —                               | —                                                                    | —                                |
| features                  | `unified-trading-features-{env}` (R/W) + `unified-trading-market-data-{env}` (R)               | none                                                                                           | —                                                                             | subscribe `market-derived-events` + publish `features-events`      | —                               | —                                                                    | —                                |
| strategy                  | `unified-trading-strategies-{env}` (R/W) + `unified-trading-features-{env}` (R)                | none                                                                                           | —                                                                             | subscribe `features-events` + publish `signals-events`             | —                               | —                                                                    | —                                |
| execution                 | `unified-trading-execution-{env}` (R/W) + DeFi config (R)                                      | **per-venue trade-scope keys + custody (Copper/Fireblocks/CEFFU) + wallet wrapped-PK secrets** | **Decrypt** on `trading-{asset_group}-master-v1` CMK (May-23 cutover signing) | subscribe `signals-events` + publish `fills-events`                | —                               | —                                                                    | —                                |
| pbms                      | `unified-trading-positions-{env}` (R/W)                                                        | per-venue read keys (balance polling)                                                          | —                                                                             | subscribe `fills-events` + publish `position-balance-events`       | —                               | —                                                                    | —                                |
| risk                      | `unified-trading-risk-{env}` (R/W)                                                             | none                                                                                           | —                                                                             | subscribe `position-balance-events` + publish `kill-switch-events` | —                               | —                                                                    | —                                |
| alerting                  | `unified-trading-alerting-{env}` (R/W)                                                         | Telegram bot token per env                                                                     | —                                                                             | subscribe all `*-events` + publish `alert-sent-events`             | —                               | —                                                                    | —                                |
| signal-broadcast          | `unified-trading-signals-broadcast-{env}` (R/W)                                                | HMAC counterparty creds + venue keys                                                           | —                                                                             | subscribe `signals-events` + publish `signal-broadcast-events`     | —                               | —                                                                    | —                                |
| deployment                | `unified-trading-deployment-{env}` (R/W) + provisions other buckets                            | Secret Manager admin (per-service creds provisioning)                                          | —                                                                             | —                                                                  | —                               | EC2 `RunInstances` + `TerminateInstances` on `uts-*` instance prefix | ECS `RunTask` on `uts-*` cluster |
| client-reporting          | `unified-trading-client-reports-{env}` (R/W) + reads features + risk + pbms                    | none                                                                                           | —                                                                             | subscribe `position-balance-events` + `fills-events`               | —                               | —                                                                    | —                                |
| trade-event               | `unified-trading-trade-events-{env}` (R/W)                                                     | none                                                                                           | —                                                                             | subscribe `fills-events`                                           | —                               | —                                                                    | —                                |
| unified-trading-system-ui | Cloud Run (Firebase mirror); GCP-side primary                                                  | Firebase SA JSON (read)                                                                        | —                                                                             | —                                                                  | —                               | —                                                                    | —                                |
| batch-live-recon          | `unified-trading-recon-{env}` (R/W) + reads all `*-events` snapshots                           | none                                                                                           | —                                                                             | subscribe all `*-events`                                           | trigger nightly recon           | —                                                                    | —                                |
| disaster-recovery         | `unified-trading-dr-{env}` (R/W)                                                               | none                                                                                           | —                                                                             | publish `dr-drill-events` + `kill-switch-events` (test scope)      | trigger DR drill cron           | —                                                                    | —                                |
| oracle-aggregation        | `unified-trading-oracle-{env}` (R/W)                                                           | Chainlink + Pyth (Hermes HTTPS only, no IAM)                                                   | —                                                                             | publish `oracle-events`                                            | —                               | —                                                                    | —                                |
| feature-onchain           | `unified-trading-features-onchain-{env}` (R/W)                                                 | Alchemy + Helius RPC keys                                                                      | —                                                                             | publish `onchain-features-events`                                  | —                               | —                                                                    | —                                |
| feature-sports            | `unified-trading-features-sports-{env}` (R/W)                                                  | api-football + footystats + soccer-football-info                                               | —                                                                             | publish `sports-features-events`                                   | —                               | —                                                                    | —                                |

---

## § 3 — Closed-set policy attachments

Per service role, attach one or more of:

- `arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy` — minimum for ECS-deployed services.
- Custom inline policy: `uts-secretsmanager-read-{env}` — `secretsmanager:GetSecretValue` on per-service-prefix secrets
  (e.g. `arn:aws:secretsmanager:ap-northeast-1:427895769566:secret:bybit-*` for execution-service).
- Custom inline policy: `uts-s3-rw-{bucket-set}-{env}` — `s3:GetObject` + `s3:PutObject` on per-service bucket set.
- Custom inline policy: `uts-sns-publish-{topic-set}-{env}` — `sns:Publish` on outgoing topics.
- Custom inline policy: `uts-sqs-consume-{queue-set}-{env}` — `sqs:ReceiveMessage` + `sqs:DeleteMessage` on incoming
  queues.
- **execution-service ONLY**: `uts-kms-decrypt-trading-cmks-{env}` — `kms:Decrypt` on
  `arn:aws:kms:ap-northeast-1:427895769566:key/<trading-{asset_group}-master-v1>` (5 CMKs). NO `kms:Encrypt` (operator
  cold-laptop wraps; service decrypts only).

---

## § 4 — Workload Identity Federation (cross-cloud)

Per Plan Phase 1.H, services running on GCP that need AWS-side resources (e.g. execution-service writing batch-vs-live
recon snapshots to AWS S3) assume the corresponding `uts-{service}-{env}` IAM role via WIF:

1. GCP SA `trading-vm-{ag}@central-element-323112.iam.gserviceaccount.com` has Workload Identity Provider Audience
   claim.
2. AWS IAM role trust policy permits `sts:AssumeRoleWithWebIdentity` from the GCP SA's OIDC token.
3. Service code uses `boto3.Session()` with the WIF token — no long-lived AWS access key on GCP VM.

---

## § 5 — Provisioning (Plan Phase 1.B — OPEN)

Terraform OR CDK SSOT at `deployment-service/terraform/aws_iam_roles/` (PENDING slot-4 successor or operator
implementation). YAML-derived config at `deployment-service/configs/aws_iam_roles.yaml` (NEW, PENDING).

Acceptance gate per Plan Phase 1.B verification:

```bash
aws iam list-roles --query 'Roles[?starts_with(RoleName, `uts-`)].RoleName'
# Expected: 19+ entries (services above) × 3 envs = ≥57 roles
```

---

## § 6 — Continuous verification

```yaml
execution:
  owner: deployment-service maintainer + ikennaigboaka (operator)
  cadence: daily cron VM `credential-probe-vm` (Phase 8.A) — extended to probe AWS IAM roles
  verifier: `aws iam get-role --role-name uts-{service}-{env}` returns matching trust policy + attached policies
  last_executed: NEVER (pending Phase 1.B operator provisioning)
```

---

## § 7 — References

- [`credentials-matrix.md`](credentials-matrix.md) — workspace credential SSOT.
- [`secret-manager-naming.md`](secret-manager-naming.md) — per-service secret naming.
- [`rotation-runbook.md`](rotation-runbook.md) — rotation cadence per IAM role.
- [`per-archetype-wallet-isolation.md`](per-archetype-wallet-isolation.md) — wallet × IAM mapping.
- [`hsm-wallet-signing.md`](hsm-wallet-signing.md) — Cloud-KMS Decrypter IAM discipline.
- [`runtime-tiers-and-deployment.md`](runtime-tiers-and-deployment.md) — deployment matrix.
- [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
  Phase 1.B + Phase 9.B.
