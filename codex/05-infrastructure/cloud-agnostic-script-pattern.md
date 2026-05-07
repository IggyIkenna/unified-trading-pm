---
title: Cloud-Agnostic Script Pattern
status: in-progress
created: 2026-05-07
last_updated: 2026-05-07
authoritative_for:
  The mandatory pattern every workspace script that touches cloud resources must follow — `--cloud {gcp,aws}` flag
  default from `CLOUD_PROVIDER` env, no direct gcloud/gsutil/google.cloud.storage without an AWS branch, UCI factory
  pattern for SDK construction.
referenced_by:
  - plans/active/aws_migration_defi_first_2026_05_07.plan.md
related:
  - codex/05-infrastructure/cloud-agnostic-audit-2026-05-07.md
  - codex/05-infrastructure/cloud-agnostic-build-lineage.md
  - codex/04-architecture/unified-cloud-interface.md
---

# Cloud-Agnostic Script Pattern

> **Status:** IN-PROGRESS — Phase 2 prep landed 2026-05-07 (cloud-providers.yaml extended for 10 missing DeFi keys;
> `deployment-service/scripts/aws/setup-defi-buckets.sh` shipped as the first AWS-side provisioning script). Subsequent
> phases populate `lib/cloud-helpers.sh` + the Python factory + the QG lint rule.

## Purpose

Every script in the workspace that touches cloud resources MUST follow a single pattern so the same script runs against
GCP today and AWS tomorrow without copy-paste. This doc is the SSOT for that pattern; the audit doc tracks which scripts
already comply.

## Scope

- Bash scripts under `scripts/`, `deployment-service/scripts/`, `*/scripts/` that talk to cloud SDKs.
- Python scripts (one-off backfills, migration tools) that import cloud SDKs.
- Cloud Run services and Lambda functions (build-time cloud selection).
- Excluded: pure-local dev scripts that never touch a cloud (test runners, lint helpers).

## The contract (1)

Every script that runs against a cloud SDK or shells out to `gcloud` / `aws` MUST accept `--cloud {gcp,aws}` with the
default resolved from `${CLOUD_PROVIDER:-gcp}`. No positional alternative; no hardcoded provider. Scripts that pre-date
this contract are tracked in [`cloud-agnostic-audit-2026-05-07.md`](./cloud-agnostic-audit-2026-05-07.md) and migrated
incrementally.

Reference shape:

```bash
CLOUD="${CLOUD_PROVIDER:-gcp}"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cloud) CLOUD="$2"; shift 2 ;;
        ...
    esac
done
case "$CLOUD" in
    gcp|aws) ;;
    *) echo "Unknown --cloud value: $CLOUD (expected gcp|aws)" >&2; exit 2 ;;
esac
```

`scripts/aws/setup-defi-buckets.sh` (shipped 2026-05-07) is AWS-only by design (its job IS to provision AWS buckets), so
it skips the `--cloud` flag — but it inherits the env-var convention (`AWS_DEFAULT_REGION`, `AWS_ACCOUNT_ID`,
`DEPLOYMENT_ENV` defaults) and reads bucket templates from the same `cloud-providers.yaml` SSOT every other script uses.

## Bash pattern (2)

Branch on `$CLOUD` per call. The intent is that no caller learns that there are two providers; only the script does.

```bash
case "$CLOUD" in
    gcp)
        gcloud storage cp "$LOCAL" "gs://${BUCKET}/${KEY}"
        ;;
    aws)
        aws s3 cp "$LOCAL" "s3://${BUCKET}/${KEY}" --region "$AWS_DEFAULT_REGION"
        ;;
esac
```

Once `deployment-service/scripts/lib/cloud-helpers.sh` lands (Phase 2 follow-up — currently empty), this branching
pattern moves into helpers (`cloud_cp_local_to_remote`, `cloud_ls_remote`, `cloud_cat_remote`) so call sites read as
single-line operations. Until then, inline branching with the case-statement above is acceptable.

## Python pattern (3)

Always use the UCI factory in `unified_trading_library.cloud_interface.factory`:

```python
from unified_trading_library.cloud_interface.factory import get_storage_client
client = get_storage_client()  # reads CLOUD_PROVIDER env; pass cloud="aws" to override
blob = client.get_blob(bucket=..., key=...)
```

Never import `from google.cloud import storage` or `import boto3` directly in service code. Tests use `@mock_aws` (moto)
for AWS or the GCS emulator for GCP — both fronted by the UCI factory.

## Bucket / object naming (4)

Bucket names come from `deployment-service/configs/cloud-providers.yaml` resolved by UCI:

```python
from unified_trading_library.cloud_interface.factory import resolve_bucket
bucket = resolve_bucket(category="dex-pools", asset_group="DEFI", env="prod")
```

The resolver substitutes `${GCP_PROJECT_ID}` / `${AWS_ACCOUNT_ID}` / `${DEPLOYMENT_ENV}` from env. The 2026-05-07
extension added 10 DeFi-relevant categories (`dex-pools`, `dex-swaps`, `evm-defi`, `eigenlayer-rewards`, `solana-defi`,
`pnl-store-defi`, `positions-store-defi`, `risk-store-defi`, `events`, `config-store`) so every read/write goes through
the SSOT. Inline `f"gs://{bucket}/..."` / `f"s3://{bucket}/..."` formatting is a violation tracked in the audit doc.

## Authentication (5)

UCI handles credential resolution per backend:

- **GCP**: ADC chain (Workload Identity → metadata server → `gcloud auth application-default login`).
- **AWS**: IAM role attached to EC2/ECS/Lambda → `~/.aws/credentials` → environment variables.

Scripts NEVER call `gcloud auth login`, `aws configure`, `aws sts assume-role` directly. Cross-cloud secret lookups
(e.g. an AWS-running service reading a GCP-resident secret during migration) go through the `MultiCloudSecretManager`
helper (Phase 4 work).

## Anti-patterns + lint rules (6)

A QG step under `base-service.sh` (Phase 1.5.D in the AWS migration plan) greps for forbidden patterns:

- `gcloud storage` outside `deployment-service/scripts/lib/cloud-helpers.sh`.
- `gsutil` anywhere (the tool is deprecated; use `gcloud storage`).
- `aws s3` / `aws s3api` outside `scripts/aws/` or `deployment-service/scripts/lib/cloud-helpers.sh`.
- `from google.cloud import storage` in service code (allowed in UCI internals only).
- `import boto3` in service code (same rule).
- Inline `f"gs://..."` / `f"s3://..."` URI formatting in any service-side Python (allowed only in
  `unified_trading_library/cloud_interface/`).

The lint is currently advisory; once Phase 1.5.D lands it becomes blocking. Until then,
`scripts/aws/setup-defi-buckets.sh`

- existing `gcloud storage` calls in launcher scripts under `deployment-service/scripts/vm/` are accepted as legacy.

## Migration plan (7)

Use [`cloud-agnostic-audit-2026-05-07.md`](./cloud-agnostic-audit-2026-05-07.md) as the punch list. The migration order
is (per the AWS migration plan Phase 1.5):

1. **1.5.A** — Bucket-name string parity audit (every consumer reads from `cloud-providers.yaml`).
2. **1.5.B** — Pub/Sub ⇄ SNS+SQS parity (UCI `MessageBus` abstraction).
3. **1.5.C** — Tarball deployment parity (CodeBuild → S3 → EC2 user-data).
4. **1.5.D** — Script-level GCS↔S3 switch (this codex doc enforces).

## Cross-references

- **Plan(s) implementing this:**
  [`aws_migration_defi_first`](../../plans/active/aws_migration_defi_first_2026_05_07.plan.md) Phase 1.5 + Phase 2.
- **Related codex SSOTs:** [`cloud-agnostic-audit-2026-05-07`](./cloud-agnostic-audit-2026-05-07.md),
  [`cloud-agnostic-build-lineage`](./cloud-agnostic-build-lineage.md).
- **Code:**
  - SSOT YAML:
    [`deployment-service/configs/cloud-providers.yaml`](../../../deployment-service/configs/cloud-providers.yaml)
  - First AWS provisioning script:
    [`deployment-service/scripts/aws/setup-defi-buckets.sh`](../../../deployment-service/scripts/aws/setup-defi-buckets.sh)
  - UCI factory: `unified-trading-library/unified_trading_library/cloud_interface/factory.py`

## Open questions

- Should we ship a `cloud-shim` wrapper that auto-translates `gcloud storage cp` → `aws s3 cp` for legacy scripts during
  the migration window? (probably no — encourages laziness)
- How strict is the lint on third-party SDK imports? Allow-list (`import boto3` allowed in `aws_*.py`-suffixed files
  only)?
- What happens for hybrid operations (read from GCS, write to S3 during dual-write window)? Pattern needs a
  `--source-cloud` + `--dest-cloud` extension.
