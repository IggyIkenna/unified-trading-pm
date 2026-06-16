---
scope: [engineer, admin]
title: Cloud-Agnostic Script Pattern
status: active
created: 2026-05-07
last_updated: 2026-05-22
authoritative_for:
  The mandatory pattern every workspace script that touches cloud resources must follow — `--cloud {gcp,aws}` flag
  default from `CLOUD_PROVIDER` env, no direct gcloud/gsutil/google.cloud.storage without an AWS branch, UCI factory
  pattern for SDK construction.
referenced_by:
  - plans/active/aws_migration_defi_first_2026_05_07.md
related:
  - codex/05-infrastructure/cloud-agnostic-audit-2026-05-07.md
  - codex/05-infrastructure/cloud-agnostic-build-lineage.md
  - codex/04-architecture/unified-cloud-interface.md
last_reviewed: 2026-05-17
---

# Cloud-Agnostic Script Pattern

> **[DELTA 2026-05-22]** **Current state:** Phase 2 prep landed (`cloud-providers.yaml` extended +
> `setup-defi-buckets.sh` shipped). `lib/cloud-helpers.sh` is still empty; the Python UCI factory and QG lint rule are
> advisory-only (not hard-error). Bucket SSOT canonicalisation (`resolve_bucket_name`) is enforced by QG STEP 5.69.
> **Planned delta:** Remaining phases tracked under `plans/epics/infrastructure_master.md`. **Target architecture:**
> Every workspace script uses `lib/cloud-helpers.sh` + UCI factory; QG lint rule is a hard error for non-compliant
> scripts.

> **Status:** ACTIVE — Phase 2 prep landed 2026-05-07 (cloud-providers.yaml extended for 10 missing DeFi keys;
> `deployment-service/scripts/aws/setup-defi-buckets.sh` shipped as the first AWS-side provisioning script). Subsequent
> phases populate `lib/cloud-helpers.sh` + the Python factory + the QG lint rule.

> **🟡 IN-FLIGHT REFACTOR — operator decision (b+) 2026-05-11.** Per
> [`plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`](../../plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md)
> Phase 0a, the env-tier convention extends to ALL buckets (Group-A `instruments-store` / `market-data` / raw-tick +
> Group-B features-\*/ml-\*/strategy/execution) across both clouds × 3 envs. New requirements for cloud-agnostic
> scripts:
>
> 1. **Every script reads `DEPLOYMENT_ENV`** (env / CLI flag) and passes it to `resolve_bucket_name(...)`. VM launcher
>    scripts MUST add a `--env <prod|staging|dev>` CLI flag (Phase 0f). Scripts that hardcode bucket names without
>    reading env are now violations.
> 2. **Same-region enforcement**: bucket provisioning scripts (`setup-buckets.sh`, Terraform) MUST reject
>    `--location=<other-region>` to keep within-cloud syncs at $0 egress (Phase 0i).
> 3. **Sync script pattern (Phase 0h)**: `deployment-service/scripts/sync-buckets-prod-to-{staging,dev}.sh` — copies
>    last `N` years of data from prod bucket to staging/dev bucket (default `N=2` for staging, `N=1` for dev).
>    Idempotent via `gsutil -n` dry-run; manifest sync follows. Truncated date window keeps dev/staging storage bill
>    5-10× cheaper than full history.
> 4. **VM launcher env-aware audit**: ~30 launchers under `deployment-service/scripts/vm/` need env-aware bucket
>    targeting; QG step (companion to STEP 5.69) AST-walks for non-helper bucket references.

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

## 4-cloud-tier discipline (4.1)

Every workload sits in exactly one of four tiers. Tier choice is part of the workload's design, not a runtime guess.

| Tier | Name                           | Examples                                                                                                                                                                                                                                                                      | Selection mechanism                                                                                                                                                                                           |
| ---- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Always-GCP                     | BigQuery analytics queries, Vertex AI training jobs, Pub/Sub subscriptions backing GCP-only operators, GCS-only legacy buckets pending S3 backfill                                                                                                                            | Hardcoded — workload imports `google.cloud.*` directly with no AWS branch. Lint rule whitelists Tier-1 modules.                                                                                               |
| 2    | Always-AWS                     | Tenderly-fork RPC integration tests, Polymarket archive S3 (no GCP equivalent), AWS Secrets Manager DeFi wallet keys post-Phase-4 mirror, ECS Fargate runtime config                                                                                                          | Hardcoded — workload imports `boto3` directly with no GCP branch. Lint rule whitelists Tier-2 modules.                                                                                                        |
| 3    | Cloud-agnostic via UCI factory | Most workspace services (MTDS, MDPS, instruments-service, features-\*, strategy-service, execution-service). Default tier.                                                                                                                                                    | Runtime selection by `CLOUD_PROVIDER` env (default `gcp`). All cloud SDK access flows through `unified_trading_library.cloud_interface.factory`.                                                              |
| 4    | Dual-cloud-active              | Backfills + manifest writers + reconcilers that run against BOTH clouds simultaneously per the 2026-05-07 operator decision: _"dual-cloud-active is the steady state, not transitional"_ (see `aws_migration_defi_first_2026_05_07.md` §"Operator answers — Phase 0 inputs"). | Per-shard fan-out: each shard write computes both `gs://...` and `s3://...` URIs and writes both. Read path picks one cloud per request via `STORAGE_READ_CLOUD_PROVIDER` env (defaults to `CLOUD_PROVIDER`). |

**Tier 3 is the default for new code.** Don't reach for Tier 1 / Tier 2 unless the workload is genuinely tied to a
single cloud's primitive. Tier 4 is opt-in for cross-cloud parity workloads — turning Tier 3 into Tier 4 is a
per-workload decision recorded in the workload's plan-of-record, not a global toggle.

## Bucket-naming SSOT — UTL `cloud_interface.bucket_naming` (4.2)

Canonical resolver (shipped 2026-05-08):

```python
from unified_trading_library.cloud_interface.bucket_naming import (
    resolve_bucket_name,    # primary lookup
    resolve_bucket_uri,     # bucket + path → "gs://..." or "s3://..."
    BucketNamingError,      # raised on unknown (cloud, asset_group, kind)
)

bucket = resolve_bucket_name(cloud="gcp", asset_group="defi", kind="raw_tick_data")
uri = resolve_bucket_uri(cloud="aws", kind="events", path="2026-05-08/foo.parquet")
# → "s3://<bucket>/2026-05-08/foo.parquet"
```

5-point contract:

1. **`deployment-service/configs/cloud-providers.yaml` is the data SSOT.** `bucket_naming.py` is the lookup logic. Never
   duplicate the per-cloud bucket templates anywhere else.
2. **Asset-group keys are lowercase in the public API** (`"cefi"`, `"defi"`, `"tradfi"`, `"sports"`, `"prediction"`) per
   CLAUDE.md asset-group vocabulary exception. The yaml internal keys are uppercase; the resolver bridges.
3. **No silent fallback** — `BucketNamingError` raised on any unknown `(cloud, asset_group, kind)`. Per CLAUDE.md "no
   try/except fallback imports".
4. **Inline `f"gs://..."` / `f"s3://..."` formatting is a violation.** Migrate to `resolve_bucket_uri`. Companion
   `seed_writer.py` refactor 2026-05-08 ships the `_format_uri()` cache pattern as the in-class precedent.
5. **`constants.py:BUCKET_PREFIXES` is deprecated.** Drifted hardcode that pre-dates the yaml SSOT. Follow-up to
   delegate `constants.get_bucket_name()` into `bucket_naming.resolve_bucket_name()` is tracked under
   `aws_migration_defi_first_2026_05_07.md` Phase 1.5.A.

Workspace anti-pattern sweep (~70 unmarked `f"gs://"` + `f"s3://"` sites + ~30 module-level `BUCKET = "..."` constants +
~600 launcher-script literals): tracked under `cloud-agnostic-audit-2026-05-07.md` § "Inline-string bucket-name audit".

## Dual-bucket dual-write rule (4.3)

Tier-4 workloads write to BOTH clouds. The pattern:

```python
from unified_trading_library.cloud_interface.bucket_naming import resolve_bucket_uri
from unified_trading_library.cloud_interface.factory import get_storage_client

def dual_write(*, kind: str, asset_group: str, path: str, payload: bytes) -> None:
    gcp_uri = resolve_bucket_uri(cloud="gcp", asset_group=asset_group, kind=kind, path=path)
    aws_uri = resolve_bucket_uri(cloud="aws", asset_group=asset_group, kind=kind, path=path)
    gcp = get_storage_client(provider="gcp")
    aws = get_storage_client(provider="aws")
    gcp_ok = _write_with_telemetry(gcp, gcp_uri, payload)
    aws_ok = _write_with_telemetry(aws, aws_uri, payload)
    if not (gcp_ok and aws_ok):
        # Hard fail per 2026-05-07 operator decision: write-failure on either
        # cloud is a hard fail. Manifest stays unrecorded; alert fires.
        raise DualWriteIncompleteError(gcp_ok=gcp_ok, aws_ok=aws_ok, gcp_uri=gcp_uri, aws_uri=aws_uri)
```

Failure-mode resolution (operator decision 2026-05-07):

| GCP write | AWS write | Action                                                                                                |
| --------- | --------- | ----------------------------------------------------------------------------------------------------- |
| ✓         | ✓         | `record_captured` in manifest as normal.                                                              |
| ✓         | ✗         | Raise `DualWriteIncompleteError`. Do NOT record manifest. Alert fires (`DUAL_WRITE_PARTIAL_FAILURE`). |
| ✗         | ✓         | Same — hard fail, no manifest record, alert.                                                          |
| ✗         | ✗         | Same — hard fail, no manifest record, alert.                                                          |

**Rationale**: a partial-success silent record creates the worst kind of phantom — the manifest says `captured` but only
one cloud has the data. Downstream reads that hit the missing cloud return empty placeholders (the 2026-05-05 MDPS
1440-NaN-bars-per-day class of bug). Hard fail forces the operator to pick one of: (a) re-run the write loop after
fixing the failed cloud's outage, (b) explicitly downgrade the workload to single-cloud Tier 3, (c) flip the failed
cloud's bucket to maintenance for the day and accept the gap.

## Storage Transfer Service config pattern (4.4)

Initial bulk migrations (Phase 5 of the AWS plan) use cloud-native transfer services rather than custom rsync loops:

**GCS → S3 (Storage Transfer Service)**:

```bash
# Reference shape; concrete config lives in deployment-service/scripts/aws/setup-defi-transfer.sh
gcloud transfer jobs create \
  gs://${GCP_PROJECT_ID}-raw-tick-data-defi \
  s3://unified-trading-raw-tick-data-defi-${ENV}-${AWS_ACCOUNT_ID} \
  --description="DeFi raw tick data — GCS→S3 initial bulk transfer" \
  --schedule-starts="$(date -u +%Y-%m-%dT%H:%MZ)" \
  --include-prefixes="asset_group=defi/" \
  --source-creds-file=/etc/sts-gcp-creds.json
```

**S3 → GCS (AWS DataSync — reverse direction)**:

```bash
# For dual-cloud-active reverse-leg: AWS-resident writes that need GCP backfill.
aws datasync create-task \
  --source-location-arn "$S3_LOCATION_ARN" \
  --destination-location-arn "$GCS_LOCATION_ARN" \
  --name "defi-aws-to-gcs-${ASSET_GROUP}-${KIND}" \
  --options "VerifyMode=ONLY_FILES_TRANSFERRED,Atime=NONE,Mtime=PRESERVE,Uid=NONE,Gid=NONE"
```

**Validation invariant** post-transfer: row-count parity ≤0.01% drift per shard via `gsutil du` ↔
`aws s3 ls --summarize` cross-check. Drift > 0.01% triggers re-transfer for the affected shards. Cost model: STS is free
for GCS→S3 (S3 charges egress on the pull side); DataSync has per-GB pricing (~$0.0125/GB transferred). Total cost for
DeFi-only initial transfer per the AWS plan §"Cost calculus" is operator-budgeted under the credit allocation.

## Per-asset_group migration sequencing (4.5)

Migration order to AWS (gated on `master_to_live_defi_2026_05_23.md` Group F + `aws_migration_defi_first_2026_05_07.md`
Phase 5-6):

1. **`defi`** — first. May-23 cutover dependency. Phase 2 buckets created at `deployment-service@7da2f3d`. Phase 5
   transfer + Phase 6 ECS Fargate deploy gate the cutover.
2. **`cefi-instruments`** — second. DeFi archetypes hedge across 6 CeFi perp venues; CeFi instruments reference data is
   on the May-23 critical path even though CeFi tick data stays GCP-resident.
3. **`cefi`-historical / `tradfi` / `sports` / `prediction`** — Phase 9 (post-cutover; see `infrastructure_master.md`).
   Opportunistic credit-utilisation. No deadline pressure.

Per-asset_group migration checklist (apply for each asset_group):

- [ ] `cloud-providers.yaml` AWS entries exist for every kind the asset_group writes (parity with `gcp.storage.<kind>`).
- [ ] `setup-{asset_group}-buckets.sh` script under `deployment-service/scripts/aws/` provisions buckets + IAM policies.
- [ ] Transfer job (GCS→S3) configured + smoke-validated on a sample shard.
- [ ] Tier-3 services for the asset_group smoke-pass with `CLOUD_PROVIDER=aws` (Phase 1.5 audit).
- [ ] Dual-write enabled on writers (Tier 3 → Tier 4 promotion).
- [ ] Manifest reconciler verifies parity at `_index/availability_index.parquet` per shard-key.
- [ ] Alerting rules cover `DUAL_WRITE_PARTIAL_FAILURE` for the asset_group's data types.

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

- **Plan(s) implementing this:** [`aws_migration_defi_first`](../../plans/active/aws_migration_defi_first_2026_05_07.md)
  Phase 1.5 + Phase 2.
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
