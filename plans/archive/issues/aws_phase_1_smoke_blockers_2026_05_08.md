---
doc_type: issue
title: AWS Phase 1 smoke blockers — bucket-name SSOT triple-drift + secrets fanout
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, instruments-service, strategy-service, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
resolved: 2026-05-10
author: tab4-aws-migration
source:
  [
    "unified-trading-pm/plans/active/aws_migration_defi_first_2026_05_07.md (Phase 1, Phase 1.5.A, Phase 2)",
    "deployment-service/scripts/aws/setup-defi-buckets.sh:62-72",
    "unified-trading-library/unified_trading_library/cloud_interface/constants.py:191-218",
    "unified-trading-library/unified_trading_library/config_interface/cloud_config.py:394",
    "unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py (UTL@780a9575 — new resolver,
    partial mitigation)",
    unified-trading-library/tests/cloud_interface/unit/test_bucket_naming.py (UTL@24f9b2cb — option c regression pin),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

> ## RESOLVED 2026-05-10 — Tab 4 option (c) shipped + verified end-to-end
>
> **Status**: ✅ RESOLVED. Bucket-naming SSOT triple-drift closed by adopting option (c) — accept the per-purpose
> 10-bucket model that `setup-defi-buckets.sh` provisions + the UTL resolver dispatches to via flat-string templates.
>
> **What shipped:**
>
> - **`cloud-providers.yaml`** already encodes the 10 DeFi purpose-specific buckets as flat-string templates under
>   `aws.storage.{dex-pools,dex-swaps,evm-defi,eigenlayer-rewards,solana-defi,pnl-store-defi,positions-store-defi,risk-store-defi,events,config-store}`
>   (verified 2026-05-10).
> - **UTL `bucket_naming.resolve_bucket_name(cloud="aws", kind=<purpose>)`** dispatches all 10 cleanly without an
>   `asset_group=` kwarg (flat-string path; verified 2026-05-10).
> - **UTL@`24f9b2cb`** lifts a regression test into `tests/cloud_interface/unit/test_bucket_naming.py` pinning the 10
>   bucket entries (parametrized) + a shape assertion that they remain flat-string templates (so a future yaml edit
>   can't silently convert one to a per-asset_group dict and force every consumer to re-pass `asset_group=`).
>
> **Phase 1 smoke verification (2026-05-10, real AWS S3, account 427895769566, region ap-northeast-1):**
>
> | Sub-smoke                                            | Result                              |
> | ---------------------------------------------------- | ----------------------------------- |
> | A · Factory swings to S3StorageClient                | ✅ PASS                             |
> | B · UTL resolver lookup for 10 DeFi purpose buckets  | ✅ 10/10 resolve                    |
> | C · `head_bucket` reachability for 10 buckets        | ✅ 10/10 reachable                  |
> | D · `list_blobs` round-trip on `evm-defi`            | ✅ no error                         |
> | E · Write/read/delete round-trip on `evm-defi`       | ✅ 50-byte payload round-trip clean |
> | F · Per-asset-group `market-data` resolver alignment | ✅ cefi/defi/tradfi all reachable   |
>
> **Smoke command (operator-runnable for re-verification):** See § "Smoke test recipe (paste-ready bash, with band-aid
> in place)" below — the band-aid env var `MARKET_DATA_S3_BUCKET_DEFI=unified-trading-evm-defi-prod-427895769566` is no
> longer required (the resolver dispatches against the yaml directly), but keeping it in the recipe doesn't hurt.
>
> **Companion blockers status:**
>
> 1. `SECRETS_CLOUD_PROVIDER` for hybrid mode → still required as documented (set `SECRETS_CLOUD_PROVIDER=gcp` when
>    running against AWS storage until Phase 4 mirror lands). Not a smoke blocker; operator runs Phase 1 smoke with
>    hybrid env.
> 2. `ATHENA_OUTPUT_BUCKET` env at construction time → still required (set to any reachable AWS bucket).
> 3. Phase 2 buckets EMPTY → still true (Phase 5 transfer hasn't run for ALL buckets); Phase 1 smoke verifies the
>    runtime mechanism, not data presence.
>
> **Pre-existing yaml drift discovered during verification (not a smoke blocker, filed as plan-body discovery):**
>
> - `cloud-providers.yaml` AWS section has `features-calendar` (single flat-string) BUT the GCP section does NOT have a
>   matching entry. The `test_workspace_yaml_has_gcp_aws_parity_for_core_kinds` regression test (lifted from sub-A's
>   audit at UTL@`780a9575`) fires on this. Suggested owner: `aws_migration_defi_first_2026_05_07.md` Phase 1.5.A — add
>   `features-calendar` to GCP yaml or remove from AWS yaml so parity holds.
>
> **No further action required on this issue doc.** Per CLAUDE.md "Plan Archival HARD RULE", the resolution above is the
> audit trail; the issue doc may be moved to `plans/archive/issues/` at the next archival sweep.

# AWS Phase 1 smoke blockers — bucket-name SSOT triple-drift + secrets fanout

> **Severity**: P0 — bucket-naming SSOT drift between (a) Phase 2 setup script, (b) UTL
> `cloud_interface/constants.py:BUCKET_PREFIXES`, (c) `UnifiedCloudConfig` per-field env-var defaults. Phase 1 smoke
> (cross-cloud parity validation for May-23 cutover) cannot succeed end-to-end without operator-blessed bucket-name
> reconciliation OR per-env-var override band-aid.
>
> **Blast radius**: UTL + deployment-service + cloud-providers.yaml SSOT + every service that resolves AWS bucket names
> (instruments-service, MTDS, features-onchain, strategy-service, position-balance-monitor, execution-service).
>
> **Suggested owner**: Tab 4 (AWS migration, Ikenna-side) for the SSOT reconciliation decision; Operator-decided which
> of 3 options to take.

## What I found

Three independent bucket-naming sources for `(market_data, defi)`:

1. **`deployment-service/scripts/aws/setup-defi-buckets.sh:62-72`** created **10 different buckets** at shape
   `unified-trading-{purpose}-{env}-{account}` — e.g. `unified-trading-dex-pools-prod-427895769566`, `-evm-defi-`,
   `-solana-defi-`, `-dex-swaps-`, `-pnl-store-defi-`, `-positions-store-defi-`, `-risk-store-defi-`, `-events-`,
   `-config-store-`, `-eigenlayer-rewards-`. These are PURPOSE-SPECIFIC, not `(kind, asset_group)`-keyed.
2. **`unified-trading-library/unified_trading_library/cloud_interface/constants.py:191-218`**
   `BUCKET_PREFIXES["aws"]["market_data"] = "unified-trading-market-data"` — would resolve to
   `unified-trading-market-data-defi-${ENV}-${ACCOUNT}` if any code path used this resolver.
3. **`unified-trading-library/unified_trading_library/config_interface/cloud_config.py:394`**
   `market_data_s3_bucket_defi: str = ""` — empty default; resolves via `MARKET_DATA_S3_BUCKET_DEFI` env var.

**None of the three agree.** A Phase 1 smoke that exercises the runtime cloud-agnostic path will fail with
`botocore.exceptions.ClientError: An error occurred (NoSuchBucket)` unless one of the three is reconciled.

UTL@`780a9575` shipped `cloud_interface/bucket_naming.py` as a yaml-backed resolver — partial mitigation: code that
calls `resolve_bucket_name(cloud="aws", asset_group="defi", kind="<kind>")` now reads from the canonical
`cloud-providers.yaml` SSOT. But the yaml itself still encodes the AWS-template shape (option 2-style), not the
purpose-specific shape that `setup-defi-buckets.sh` actually created. The drift is between **the script** and **the
yaml**, not between **the yaml** and **the resolver**.

## Why it matters

Phase 1 smoke is the readiness gate for May-23 AWS↔GCP parity. Until the script-vs-yaml drift is reconciled, no
AWS-resident parquet read can succeed end-to-end without per-deployment env-var overrides, which themselves are a
band-aid that violates the SSOT contract codified at
[`/codex/05-infrastructure/cloud-agnostic-script-pattern.md`](/codex/05-infrastructure/cloud-agnostic-script-pattern.md)
§ "Bucket-naming SSOT (4.2)".

Long-term, all three sources must converge on ONE shape. Three options for triage:

## Recommended decision

**Operator triage call needed** — pick one of:

- **(a) Update setup-defi-buckets.sh + `cloud-providers.yaml` to match `BUCKET_PREFIXES` shape (rename buckets).** Cost:
  requires renaming 10 already-provisioned buckets (or deleting + recreating). Easiest from a code-shape perspective but
  costs wall-clock time on the May-23 critical path. Buckets are empty (Phase 5 transfer hasn't run) so the rename has
  no data-side cost — just AWS-side bucket destruction + recreation.
- **(b) Update `BUCKET_PREFIXES` + `cloud-providers.yaml` to match the 10 already-created buckets.** Cost: refactor
  `cloud_interface/constants.py:BUCKET_PREFIXES` to a per-purpose shape rather than per-kind. May need to extend
  `resolve_bucket_name()` API to take a `purpose` arg in addition to `(cloud, asset_group, kind)`. Some semantic loss
  (the kind→purpose mapping isn't 1:1).
- **(c) Accept that DeFi uses 10 purpose-specific buckets** (`dex-pools`, `dex-swaps`, `evm-defi`, `solana-defi`,
  `eigenlayer-rewards`, `pnl-store-defi`, `positions-store-defi`, `risk-store-defi`, `events`, `config-store`) and
  refactor the resolver to dispatch by sub-domain. **Most aligned with Phase 2 intent** + reflects the per-purpose
  bucket model that `setup-defi-buckets.sh` shipped. Requires `resolve_bucket_name()` API extension and a one-time YAML
  restructure to the per-purpose shape.

**Tab 4 recommendation**: Option **(c)**. Phase 2's per-purpose bucket model is the deliberate decision encoded in the
provisioning script; the constants.py `BUCKET_PREFIXES` is a drifted hardcode that pre-dates Phase 2. Migrating the SSOT
to match Phase 2 intent (rather than reverting Phase 2 to match the older hardcode) is the forward-looking call.

## Companion blockers (also surfaced 2026-05-08 audit)

1. **`SECRETS_CLOUD_PROVIDER` not declared/wired for hybrid mode.** Factory supports per-resource provider override
   (`secrets_cloud_provider`, `storage_cloud_provider` fields in `UnifiedCloudConfig`). For Phase 1 we want secrets on
   GCP (Phase 4 hasn't replicated them yet) while storage probes AWS. Smoke recipe must set `SECRETS_CLOUD_PROVIDER=gcp`
   explicitly when `CLOUD_PROVIDER=aws`. Otherwise services that read API keys (Tardis, Databento, IBKR) hit empty AWS
   Secrets Manager.
2. **`ATHENA_OUTPUT_BUCKET` env required at construction time.** Any code path that imports `AWSAnalyticsClient` raises
   `ValueError` if unset. Smoke recipe must export it (any AWS bucket the operator's account can write to;
   `unified-trading-events-prod-427895769566` is a sensible default).
3. **Phase 2 buckets are EMPTY.** Phase 5 (GCS→S3 transfer) hasn't run. Phase 1 smoke must be designed around this —
   verify the **mechanism** (boto3 client constructs, region resolves, head_bucket succeeds, `list_blobs` returns empty
   without error) rather than expect populated data.

## Smoke test recipe (paste-ready bash, with band-aid in place)

Until SSOT triage option lands, operator can run this band-aid recipe to validate the runtime path:

```bash
# === AWS Phase 1 cross-cloud parity smoke — band-aid mode ===

# Auth check
aws sts get-caller-identity --output text  # expect 427895769566

# Env (the runtime swing)
export CLOUD_PROVIDER=aws
export AWS_ACCOUNT_ID=427895769566
export AWS_DEFAULT_REGION=ap-northeast-1
export AWS_REGION=ap-northeast-1
# Hybrid: keep secrets on GCP until Phase 4 mirror lands
export SECRETS_CLOUD_PROVIDER=gcp
export GCP_PROJECT_ID=central-element-323112
# Athena needs an output bucket even if we don't use it
export ATHENA_OUTPUT_BUCKET=unified-trading-events-prod-427895769566
# Pick a bucket the Phase 2 script actually created (BAND-AID — required until SSOT triage lands)
export MARKET_DATA_S3_BUCKET_DEFI=unified-trading-evm-defi-prod-427895769566

# Activate workspace venv
cd "${UNIFIED_TRADING_WORKSPACE_ROOT:-$HOME/Code/unified-trading-system-repos}"
source .venv-workspace/bin/activate

# Smoke A — factory swings to S3StorageClient
python -c "
from unified_trading_library.cloud_interface.factory import get_storage_client
client = get_storage_client()
print('CLASS:', client.__class__.__name__)
assert client.__class__.__name__ == 'S3StorageClient'
print('PASS — factory routed to AWS S3StorageClient')
"

# Smoke B — bucket reachability
python -c "
import os
from unified_trading_library.cloud_interface.factory import get_storage_client
bucket = get_storage_client().bucket(os.environ['MARKET_DATA_S3_BUCKET_DEFI'])
assert bucket.exists()
print('PASS — bucket reachable')
"

# Smoke C — list_blobs round-trip (empty OK)
python -c "
import os
from unified_trading_library.cloud_interface.factory import get_storage_client
client = get_storage_client()
list(client.list_blobs(os.environ['MARKET_DATA_S3_BUCKET_DEFI'], max_results=5))
print('PASS — list_blobs returned without error')
"

# Smoke D — write/read/delete round-trip (proves IAM + KMS + region)
python -c "
import os, time
from unified_trading_library.cloud_interface.factory import get_storage_client
bucket = os.environ['MARKET_DATA_S3_BUCKET_DEFI']
key = f'_smoke/{int(time.time())}.txt'
payload = b'aws-phase-1-smoke-2026-05-08'
client = get_storage_client()
client.upload_bytes(bucket, key, payload, content_type='text/plain')
assert client.download_bytes(bucket, key) == payload
client.delete_blob(bucket, key)
print('PASS — write/read/delete roundtrip clean')
"
```

**Pass criteria**: A, B, C, D all print `PASS`. **Fail signals**: `NoCredentialsError` (auth not set), `NoSuchBucket`
(bucket-name SSOT drift not band-aided), `Could not connect to the endpoint URL` (region/network mismatch).

## Cross-references

- [`/codex/05-infrastructure/cloud-agnostic-script-pattern.md`](/codex/05-infrastructure/cloud-agnostic-script-pattern.md)
  § "4-cloud-tier discipline" + § "Bucket-naming SSOT (4.2)".
- [`/codex/05-infrastructure/cloud-agnostic-audit-2026-05-07.md`](/codex/05-infrastructure/cloud-agnostic-audit-2026-05-07.md)
  § "Inline-string bucket-name audit (2026-05-08)" + § "AWS Phase 1 smoke readiness".
- [`plans/active/aws_migration_defi_first_2026_05_07.md`](../aws_migration_defi_first_2026_05_07.md) Phase 1 + Phase
  1.5.A + Phase 2 + Phase 5.
- UTL@`780a9575` (bucket_naming.py — partial mitigation).
- `deployment-service/scripts/aws/setup-defi-buckets.sh` (Phase 2 provisioning).
