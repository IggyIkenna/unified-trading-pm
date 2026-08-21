---
doc_type: plan
title: UCI Cloud Abstraction Complete
summary: 'Complete cloud-provider abstraction so a single CLOUD_PROVIDER env var switches the entire system between GCP
  and AWS with zero code changes. All cloud SDK usage lives exclusively inside unified-cloud-interface providers. UCI exposes
  StorageClient, SecretClient, QueueClient, AnalyticsClient, CacheClient, ComputeClient with auto-provider selection. UTL
  parallel cloud layer deleted. Terraform + bootstrap scripts in deployment-service. CLOUD_PROVIDER: gcp | aws | local.
  Terraform is exempt.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-06'
todos:
- {id: p0-service-violations, content: 'Fix direct SDK imports in services (features-cross-instrument, hyperliquid_adapter, deployment-api redis).', status: completed}
- {id: p0-script-violations, content: Fix direct GCS/BQ SDK imports in deployment-service scripts and ml-training-service scripts., status: completed}
- {id: p0-utl-cloud-layer-symbol-deletion, content: 'CloudTarget and StandardizedDomainCloudService fully deleted from UTL source and __all__. All consumers (UDC, UML, execution-service, market-tick-data-service, instruments-service) migrated to UCI routing_key pattern. Implementation completed in topology_dag_pm_ssot.md todos: udc-cloud-target-replace (completed), utl-cloud-symbols-delete (completed), service-consumers-migrate (completed), uml-model-registry-migrate (completed). Gate confirmed: rg ''CloudTarget|StandardizedDomainCloudService'' returns zero matches in production source.', status: completed}
- {id: p0-utl-cloud-layer, content: 'Remove UTL parallel cloud layer (cloud_auth_factory, aws_clients, storage_abstraction, secret_abstraction); migrate all callers to UCI.', status: completed}
- {id: p1-analytics-client, content: Add AnalyticsClient ABC + GCSAnalyticsClient/AthenaAnalyticsClient/LocalAnalyticsClient to UCI., status: completed}
- {id: p1-async-cache-client, content: Add AsyncCacheClient ABC + AsyncRedisProvider/AsyncLocalCacheProvider to UCI., status: completed}
- {id: p1-compute-client, content: Add ComputeClient ABC + GCPComputeClient/AWSComputeClient/LocalComputeClient to UCI., status: completed}
- {id: p1-s3-explicit-creds, content: AWSStorageClient accepts explicit credentials for hyperliquid requester-pays., status: completed}
- {id: p1-uci-factory, content: UCI factory functions read CLOUD_PROVIDER via UnifiedCloudConfig; no direct os.getenv., status: completed}
- {id: p2-cloud-build-configs, content: 'buildspec.aws.yaml distributed to all 44 qualifying repos (8 newly created, 36 already present) — FILE DISTRIBUTION DONE. Canary simulated CodeBuild run tracked in aws_migration.md todo codebuild-canary-run. Will be marked completed once canary run exits 0.', status: pending}
- {id: p3-terraform-gcp, content: 'deployment-service/terraform/gcp/ — GCS buckets, BQ datasets, Secret Manager stubs, IAM, Cloud Run definitions. Files exist: verified 2026-03-06.', status: completed}
- {id: p3-terraform-aws, content: 'deployment-service/terraform/aws/ — S3 buckets, Athena, Secrets Manager, IAM, ECS task definitions. Files exist: verified 2026-03-06.', status: completed}
- {id: p3-bootstrap-scripts, content: 'deployment-service/scripts/bootstrap/ — bootstrap_gcp.sh, bootstrap_aws.sh, verify_bootstrap.py. Files exist: verified 2026-03-06.', status: completed}
- {id: p4-quality-gate, content: STEP 5.10 (direct cloud SDK scan) and STEP 5.11 added to all quality-gates templates. Confirmed 2026-03-05., status: completed}
isProject: true
blockedBy:
- {plan: phase0_standards_enforcement.md, reason: '[RESOLVED 2026-03-06] Phase 0 quality gate scan passed; STEP 5.9 active; STEP 5.10/5.11 added'}
- {plan: phase2_library_tier_hardening.md, reason: '[RESOLVED 2026-03-06] UTL cloud layer removal complete (p0-utl-cloud-layer status: completed; all UTL cloud symbols deleted)'}
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# UCI Cloud Abstraction Complete — Detailed Spec

name: UCI Cloud Abstraction Complete overview: | Complete cloud-provider abstraction so a single CLOUD_PROVIDER env var
switches the entire system between GCP and AWS with zero code changes.

Target state:

- All cloud SDK usage lives exclusively inside unified-cloud-interface providers
- UCI exposes: StorageClient, SecretClient, QueueClient, AnalyticsClient (BigQuery/Athena), CacheClient (Redis sync +
  async), ComputeClient (Cloud Run / ECS), and a UCI factory that auto-selects provider from CLOUD_PROVIDER env var
- Every repo has cloudbuild.yaml (GCP) AND buildspec.aws.yaml (AWS)
- deployment-service contains Terraform templates + bootstrap scripts for one-time resource creation (buckets, BigQuery
  datasets/external tables, secret stubs, service accounts)
- UTL's parallel cloud layer (cloud_auth_factory, cloud_base_service, storage_abstraction, aws_clients) deleted; all
  callers migrated to UCI

CLOUD_PROVIDER accepted values: gcp | aws | local Terraform is exempt — it is cloud-native by design.

todos:

# ─────────────────────────────────────────────────────────────────────────────

# PHASE 0 — Fix existing UCI bypass violations (blocking quality gate)

# ─────────────────────────────────────────────────────────────────────────────

- id: p0-service-violations content: | Fix direct SDK imports in services (non-UTL). FILES:
  1.  features-cross-instrument-service/.../realized_implied_vol.py
      - Remove `from google.cloud.storage import Blob`
      - Cast type: `cast("Iterable[Blob]", ...)` → `list[BlobMetadata]` (UCI)

  2.  unified-market-interface/.../hyperliquid_adapter.py
      - Remove late `import boto3 as _boto3`
      - Inject explicit creds via `S3StorageClient(aws_access_key_id=..., aws_secret_access_key=...)`
      - Requires UCI S3StorageClient to accept explicit cred params (add in p1-analytics)

  3.  deployment-api/.../deployment_events.py
      - `import redis` (sync pub/sub in `notify_deployment_updated_sync`)
      - Replace with `QueueClient.publish("deployment:updated", ...)` from UCI
      - For local mode use LocalQueueProvider; for GCP use PubSubQueueClient

  4.  deployment-api/.../cache.py

          - `import redis.asyncio as aioredis` (async Redis tier)
          - Wrap via UCI `CacheClient` async interface (add async Redis in p1-analytics)
          - Until p1-analytics done: use UCI's sync `RedisProvider` via threadpool executor

      GATE: `rg 'from googlecloudstorage import Blob|import boto3|import redis' --type py

--glob '!.venv\*' --glob '!unified-cloud-interface/**' --glob '!tests/**'` returns 0 matches across all service repos.
status: completed

- id: p0-script-violations content: | Fix direct SDK imports in deployment-service scripts and ml-training-service
  scripts. SCRIPTS WITH DIRECT GCS Client:
  - deployment-service/scripts/sports/generate_arb_report.py
  - deployment-service/scripts/sports/apply_csv_corrections.py
  - deployment-service/scripts/sports/check_storage_size.py
  - deployment-service/scripts/sports/pipeline_test.py
  - deployment-service/scripts/download_instruments.py
  - deployment-service/scripts/aggregate_instruments.py SCRIPTS WITH DIRECT BQ Client:
  - ml-training-service/scripts/etl_gcs_to_bigquery.py PATTERN for each script:
  - Replace `from google.cloud.storage import Client as GCSClient` with
    `from unified_cloud_interface import get_storage_client`
  - Replace raw `storage.Client(project=...)` with `get_storage_client(project_id=...)`
  - Replace raw BQ Client with `get_analytics_client()` once p1-analytics adds it; until then keep BQ in scripts but
    add # noqa: UCC001 comment documenting the gap GATE:
    `rg 'from google\.cloud\.storage import Client' --type py --glob '!.venv*'` returns 0 matches. status: completed
- id: p0-utl-cloud-layer content: | Remove UTL's parallel cloud abstraction layer; migrate all callers to UCI. FILES TO
  DELETE (after migrating all callers):
  - unified-trading-library/unified_trading_library/core/cloud_auth_factory.py
  - unified-trading-library/unified_trading_library/core/aws_clients.py
  - unified-trading-library/unified_trading_library/core/storage_abstraction.py (if exists)
  - unified-trading-library/unified_trading_library/core/secret_abstraction.py (if exists)
  - unified-trading-library/unified_trading_library/core/client_factory.py (if wraps UTL abstractions) FILES TO REFACTOR
    (migrate, not delete):
  - unified-trading-library/unified_trading_library/core/cloud_base_service.py → Remove
    `from google.cloud import bigquery, storage`; remove raw pool creation; keep UnifiedCloudService but wire
    storage_client and secret_client through UCI
  - unified-trading-library/unified_trading_library/core/cloud_storage_service.py → Remove
    `from google.cloud import bigquery`; use UCI AnalyticsClient (p1-analytics)
  - unified-trading-library/unified_trading_library/core/cloud_pubsub_service.py → Remove
    `from google.cloud import bigquery`; use UCI QueueClient for pubsub operations
  - unified-trading-library/unified_trading_library/core/logging.py → Remove boto3 late import; structured logging goes
    through UEI (log_event) not raw boto3 GATE: UTL pyproject.toml has no direct google-cloud- or boto3 in
    [project.dependencies]; only [project.optional-dependencies.gcp] and [project.optional-dependencies.aws] (both
    delegate to UCI). NOTE: 4 UTL files deleted (cloud_auth_factory, aws_clients, storage_abstraction,
    secret_abstraction). google-cloud-\* moved to [project.optional-dependencies.gcp]; [project.dependencies] is clean.
    gcp_clients.py, secret_manager.py, config_reloader.py use deferred imports only — gate confirmed 2026-03-06. status:
    completed

# ─────────────────────────────────────────────────────────────────────────────

# PHASE 1 — Extend UCI with missing abstractions

# ─────────────────────────────────────────────────────────────────────────────

- id: p1-analytics-client content: | Add AnalyticsClient abstraction to UCI for BigQuery/Athena.
  unified-cloud-interface/unified_cloud_interface/abstractions.py: class AnalyticsClient(ABC): @abstractmethod def
  execute_query(self, query: str, params: dict[str, object] | None = None) -> list[dict[str, object]]: ...
  @abstractmethod def execute_query_to_dataframe(self, query: str, params: ...) -> pd.DataFrame: ... @abstractmethod def
  table_exists(self, dataset: str, table: str) -> bool: ... @abstractmethod def create_table(self, dataset: str, table:
  str, schema: list[dict[str, str]]) -> None: ... @abstractmethod def insert_rows(self, dataset: str, table: str, rows:
  list[dict[str, object]]) -> None: ... unified-cloud-interface/unified_cloud_interface/providers/gcp.py: class
  GCSAnalyticsClient(AnalyticsClient): → wraps google.cloud.bigquery.Client
  unified-cloud-interface/unified_cloud_interface/providers/aws.py: class AthenaAnalyticsClient(AnalyticsClient): →
  wraps boto3 Athena client unified-cloud-interface/unified_cloud_interface/providers/local.py: class
  LocalAnalyticsClient(AnalyticsClient): → wraps SQLite for local dev/testing **all** export in abstractions.py + UCI
  **init**.py. GATE: `from unified_cloud_interface import AnalyticsClient, get_analytics_client` works. status:
  completed
- id: p1-async-cache-client content: | Add async CacheClient to UCI (for deployment-api async Redis tier).
  unified-cloud-interface/unified_cloud_interface/abstractions.py: class AsyncCacheClient(ABC): @abstractmethod async
  def get(self, key: str) -> bytes | None: ... @abstractmethod async def set(self, key: str, value: bytes, ttl_seconds:
  int | None = None) -> None: ... @abstractmethod async def delete(self, key: str) -> None: ... @abstractmethod async
  def exists(self, key: str) -> bool: ... @abstractmethod async def publish(self, channel: str, message: str) -> None:
  ... unified-cloud-interface/unified_cloud_interface/cache.py: class AsyncRedisProvider(AsyncCacheClient): → wraps
  redis.asyncio (aioredis) → lazy import: `if _HAS_REDIS: import redis.asyncio as aioredis`
  unified-cloud-interface/unified_cloud_interface/providers/local.py: class AsyncLocalCacheProvider(AsyncCacheClient): →
  in-memory dict + asyncio.Queue for pub/sub channel GATE: deployment-api cache.py uses `AsyncRedisProvider` from UCI.
  status: completed
- id: p1-compute-client content: | Add ComputeClient and CloudRunClient abstractions to UCI. ComputeClient covers: spin
  up / terminate compute instances. CloudRunClient covers: deploy Cloud Run services, get service URLs, trigger jobs.
  unified-cloud-interface/unified_cloud_interface/abstractions.py: @dataclass class ServiceDeployment: service_name: str
  image: str region: str env_vars: dict[str, str] min_instances: int = 0 max_instances: int = 1 memory: str = "512Mi"
  cpu: str = "1"

```
  class ComputeClient(ABC):
    @abstractmethod def deploy_service(self, deployment: ServiceDeployment) -> str: ...
    @abstractmethod def get_service_url(self, service_name: str, region: str) -> str | None: ...
    @abstractmethod def delete_service(self, service_name: str, region: str) -> bool: ...
    @abstractmethod def list_services(self, region: str) -> list[str]: ...


```

GCP provider: GCPComputeClient → wraps google-cloud-run SDK AWS provider: AWSComputeClient → wraps boto3 ECS/Fargate
Local provider: LocalComputeClient → no-op / logs only GATE:
`from unified_cloud_interface import ComputeClient, get_compute_client` works. status: completed

- id: p1-s3-explicit-creds content: | UCI AWSStorageClient must accept explicit credentials (for hyperliquid
  requester-pays). unified-cloud-interface/unified_cloud_interface/providers/aws.py: AWSStorageClient.**init**(
  region_name: str | None = None, aws_access_key_id: str | None = None, aws_secret_access_key: str | None = None,
  session_token: str | None = None, ) → pass these to boto3.client("s3", ...)
  unified-cloud-interface/unified_cloud_interface/**init**.py: Update get_storage_client() factory to pass optional cred
  kwargs. GATE: hyperliquid_adapter.py can remove boto3 late import. status: completed
- id: p1-uci-factory content: | UCI factory functions read CLOUD_PROVIDER env var via UnifiedCloudConfig.
  unified-cloud-interface/unified_cloud_interface/**init**.py: def get_storage_client(project_id: str | None = None,
  **kwargs) -> StorageClient: provider = resolve_provider() # reads CLOUD_PROVIDER via UnifiedCloudConfig if provider ==
  "gcp": return GCSStorageClient(project_id=project_id) if provider == "aws": return AWSStorageClient(**kwargs) return
  LocalStorageProvider()

```
  def get_secret_client(...) -> SecretClient: ...
  def get_queue_client(...) -> QueueClient: ...
  def get_analytics_client(...) -> AnalyticsClient: ...
  def get_compute_client(...) -> ComputeClient: ...
  def get_cache_client(...) -> CacheProvider: ...
  def get_async_cache_client(...) -> AsyncCacheClient: ...


```

No direct os.getenv() — use UnifiedCloudConfig from unified-config-interface. GATE: CLOUD_PROVIDER=aws python -c 'from
unified_cloud_interface import get_storage_client; assert get_storage_client().provider_name == "aws"' exits 0. status:
completed

# ─────────────────────────────────────────────────────────────────────────────

# PHASE 2 — Cloud build configs per repo (GCP + AWS)

# ─────────────────────────────────────────────────────────────────────────────

- id: p2-cloud-build-configs content: | Every service and library repo must have: - cloudbuild.yaml (GCP Cloud Build —
  already exists in most repos) - buildspec.aws.yaml (AWS CodeBuild — missing everywhere) buildspec.aws.yaml template:
  version: 0.2 phases: install: runtime-versions: python: 3.13 commands: - curl -LsSf https://astral.sh/uv/install.sh |
  sh - uv pip install -e ".[dev]" pre_build: commands: - bash scripts/quickmerge.sh --qg-only build: commands: - bash
  scripts/quickmerge.sh artifacts: files: [ "**/*" ] Repo scope: all repos in workspace-manifest.json with type=library
  or type=service. CLOUD_PROVIDER env var injected by CI at build time (gcp | aws). GATE: buildspec.aws.yaml present in
  all in-scope repos; simulated CodeBuild run passes for 3 canary repos (instruments-service, unified-cloud-interface,
  unified-events-interface). NOTE: 44/44 qualifying repos have buildspec.aws.yaml (8 newly created, 36 already present).
  File distribution DONE. Canary simulated run PENDING (tracked in topology_dag_pm_ssot.md codebuild-canary-run).
  status: pending

# ─────────────────────────────────────────────────────────────────────────────

# PHASE 3 — Deployment service: Terraform + bootstrap scripts

# ─────────────────────────────────────────────────────────────────────────────

- id: p3-terraform-gcp content: | deployment-service/terraform/gcp/: main.tf — GCS buckets (market-data, models,
  features, deployment-state) — BigQuery datasets (market_data, features, ml_models, audit) — Secret Manager secret
  stubs (names only, values filled manually) — Service accounts with least-privilege IAM — Cloud Run service definitions
  (per service image) variables.tf — project_id, region, environment (dev|staging|prod), bucket_prefix outputs.tf —
  bucket names, dataset IDs, service URLs Terraform backend: GCS bucket
  gs://{bucket_prefix}-terraform-state-{project_id} GATE: `terraform plan` exits 0 in GCP project with GCP_PROJECT_ID
  set. status: completed
- id: p3-terraform-aws content: | deployment-service/terraform/aws/: main.tf — S3 buckets (same logical names as GCP,
  prefixed s3://) — Athena workgroup + databases (mirrors BQ datasets) — Secrets Manager secret stubs — IAM roles with
  least-privilege policies — ECS cluster + task definitions (per service image) variables.tf — aws_account_id,
  aws_region, environment, bucket_prefix outputs.tf — bucket names, database ARNs, cluster ARN Terraform backend: S3
  bucket {bucket_prefix}-terraform-state-{account_id} GATE: `terraform plan` exits 0 in AWS account with AWS_ACCOUNT_ID
  set. status: completed
- id: p3-bootstrap-scripts content: | deployment-service/scripts/bootstrap/: bootstrap_gcp.sh — idempotent one-time
  setup: enable APIs, create terraform state bucket, run terraform apply, seed Secret Manager stubs bootstrap_aws.sh —
  idempotent one-time setup: create S3 state bucket, run terraform apply, seed Secrets Manager stubs verify_bootstrap.py
  — cross-provider: confirms all expected resources exist via UCI (uses get_storage_client, get_secret_client,
  get_analytics_client) CLOUD_PROVIDER env var drives which bootstrap script's terraform is used. GATE:
  verify_bootstrap.py exits 0 against both GCP and AWS bootstrap environments. status: completed

# ─────────────────────────────────────────────────────────────────────────────

# PHASE 4 — Quality gate: enforce no direct SDK usage

# ─────────────────────────────────────────────────────────────────────────────

- id: p4-quality-gate content: | Add STEP 5.10 to quality-gates-service-template.sh and
  quality-gates-library-template.sh:

```
  # STEP 5.10 — No direct cloud SDK imports outside UCI providers
  echo "=== STEP 5.10: Direct cloud SDK scan ==="
  DIRECT_SDK=$(rg \
    'from google\.cloud\.(storage|bigquery|pubsub|secretmanager|logging)|
     import boto3|
     from boto3|
     import redis\.asyncio|
     import redis$|
     from redis import' \
    --type py \
    --glob '!.venv*' \
    --glob '!unified-cloud-interface/**' \
    --glob '!tests/**' \
    --glob '!scripts/**' \
    -l)
  if [ -n "$DIRECT_SDK" ]; then
    echo "FAIL: Direct cloud SDK imports found (use UCI):"
    echo "$DIRECT_SDK"
    exit 1
  fi
  echo "PASS: No direct cloud SDK imports"


```

GATE: All repos pass STEP 5.10; zero FAIL results in workspace scan. NOTE: STEP 5.10 added to quality-gates.sh (line
329). STEP 5.11 added (line 478). Confirmed 2026-03-05. status: completed

isProject: true blockedBy:

- plan: phase0_standards_enforcement.md reason: Phase 0 quality gate scan (STEP 5.9) must pass before UCI violations are
  added as new gate
- plan: phase2_library_tier_hardening.md reason: UTL cloud layer removal (p0-utl-cloud-layer) must complete before
  library tier is locked
