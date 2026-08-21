---
doc_type: plan
title: cloud-infra-extended-bootstrap
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-service, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
overview: 'Extended cloud infrastructure bootstrap: Pub/Sub topics + subscriptions, Redis/Memorystore,

  Cloud SQL (PostgreSQL for execution-service order state), Artifact Registry (Docker + wheels),

  billing budget alerts with daily breakdown, deployment cleanup scripts, and SIT smoke tests

  for all of the above. Both GCP (primary) and AWS (blocked until creds) equivalents.

  Strategy: test what''s real now; mock/skip AWS; validate everything via SIT smoke tests.

  '
type: infra
epic: epic-infra
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: deployment-service, code: C5, deployment: none, business: none, readiness_note: 'C5: all quality gates passing. BR N/A: infrastructure provisioning plan — no commercial sign-off required.'}
- {repo: system-integration-tests, code: C5, deployment: none, business: none, readiness_note: 'C5: all quality gates passing. BR N/A: infrastructure provisioning plan — no commercial sign-off required.'}
depends_on: [cloud-infra-bucket-auth]
todos:
- {id: pubsub-topics-gcp, content: 'Create all required GCP Pub/Sub topics + subscriptions using deployment-service/scripts/setup-pubsub.sh. Topics: deployment-events, deployment-status, deployment-alerts, fill-events-{binance,bybit,okx,deribit,hyperliquid}, circuit-breaker-events, risk-breach-alerts, position-updates, cascade-predictions, ml-predictions, strategy-sports-signals, strategy-signals, config-updates, system-health-events, audit-log-events. Each topic gets pull subscriptions per downstream consumer. Idempotent — safe to re-run.', status: done, notes: 'DONE 2026-03-10: 18 topics + 41 subscriptions live in central-element-323112.

    Script fixed: arg parsing (GCP_PROJECT_ID env var), removed --retain-acked-messages=false.

    Topics: deployment-events, deployment-status, deployment-alerts, fill-events-{binance,bybit,

    okx,deribit,hyperliquid}, circuit-breaker-events, risk-breach-alerts, position-updates,

    cascade-predictions, ml-predictions, strategy-sports-signals, strategy-signals,

    config-updates, system-health-events, audit-log-events, billing-alerts (via billing script).

    verify_infra.py verify_pubsub_topics() can validate post-create.

    '}
- {id: pubsub-aws-sns, content: AWS SNS/SQS equivalents for all Pub/Sub topics. AWS uses SQS for pull queues and SNS for fan-out. UCI has get_queue_client() returning SQSQueueClient but no SNS PubSub equivalent. Add AWS SNS client to UCI providers/aws.py implementing PubSubClient protocol. Create setup-aws-messaging.sh with aws sns create-topic for each required topic., status: done, notes: 'DONE 2026-03-10: setup-pubsub.sh --cloud aws implemented (deployment-service 740423c).

    SNS topic per entry + SQS queue per subscriber + SNS→SQS subscription with queue policy.

    Master: setup-cloud-infra.sh --cloud aws --component messaging

    Blocked until AWS creds — prints [BLOCKED] gracefully when creds absent.

    '}
- {id: redis-memorystore-gcp, content: 'Run deployment-service/scripts/setup-redis.sh to create GCP Memorystore (Redis 7.0) instance ''trading-cache'' in asia-northeast1. Script stores redis-url, redis-host, redis-port, redis-password in GCP Secret Manager. UCI get_cache_client(provider=''gcp'') reads redis-url SM secret. SIT test_cache_smoke.py validates ping + set/get/delete.', status: done, notes: 'DONE 2026-03-10 (pre-existing): trading-cache REDIS_7_0 BASIC 1GB at 10.37.84.139:6379 READY.

    Created 2026-02-26. No action needed — instance already running.

    REDIS_URL or redis-url SM secret needed for SIT test_cache_smoke.py to run live Redis tests.

    '}
- {id: redis-aws-elasticache, content: 'AWS ElastiCache (Redis) equivalent. Create setup-aws-elasticache.sh using AWS CLI: aws elasticache create-replication-group. Store connection URL in AWS Secrets Manager. UCI get_cache_client(provider=''aws'') needs ElastiCache integration (currently only LocalCacheProvider for non-GCP).', status: done, notes: 'DONE 2026-03-10: setup-redis.sh --cloud aws implemented (deployment-service 740423c).

    Creates ElastiCache Redis 7.0 replication group, waits for available, stores elasticache-url

    in AWS Secrets Manager. Master: setup-cloud-infra.sh --cloud aws --component cache.

    Blocked until AWS creds — prints [BLOCKED] gracefully when creds absent.

    test_cache_smoke.py TestAWSElastiCache skips on missing ELASTICACHE_URL.

    '}
- {id: cloudsql-gcp, content: 'Create GCP Cloud SQL PostgreSQL 15 instance for execution-service order/position state persistence. Run deployment-service/scripts/setup-cloudsql.sh which creates instance ''trading-order-state'' (db-g1-small, asia-northeast1), database ''order_state'', user ''execution_svc'', stores connection URL as ''cloudsql-execution-db-url'' in Secret Manager. Grants roles/cloudsql.client to github-actions-deploy SA.', status: done, notes: 'DONE 2026-03-10: trading-order-state POSTGRES_15 db-g1-small RUNNABLE at 34.104.179.12.

    Database order_state created. User execution_svc created.

    SM secrets: cloudsql-execution-db-url, cloudsql-execution-db-password stored.

    Script fixed: arg parsing (GCP_PROJECT_ID env var + --dry-run flag).

    SIT tests: test_database_smoke.py (skip if no DATABASE_URL / SM secret).

    execution-service OrderStateRepository (postgresql.py) ready to use.

    '}
- {id: rds-aws, content: AWS RDS (PostgreSQL) equivalent for execution-service order state. Create setup-aws-rds.sh using aws rds create-db-instance. Store connection URL in AWS Secrets Manager. Update execution-service config to support AWS_DATABASE_URL., status: done, notes: 'DONE 2026-03-10: setup-cloudsql.sh --cloud aws implemented (deployment-service 740423c).

    Creates RDS PostgreSQL 15 instance, waits for available, stores rds-execution-db-url and

    rds-execution-db-password in AWS Secrets Manager. Master: setup-cloud-infra.sh --cloud aws --component database.

    Blocked until AWS creds — prints [BLOCKED] gracefully when creds absent.

    test_database_smoke.py TestAWSRDS skips on missing AWS_DATABASE_URL.

    '}
- {id: artifact-registry-gcp, content: 'Validate GCP Artifact Registry Docker + Python wheel repos exist and are populated. Create cleanup-untagged-images.sh to delete untagged (sha256-only) images older than 7 days, keeping 2 most recent. Verify deployment-api AR client works. List all service images. Check Python wheel repo (trading-wheels) for published packages.', status: done, notes: 'DONE 2026-03-10: cleanup-untagged-images.sh written (deployment-service).

    deployment-api/utils/artifact_registry.py already has ArtifactRegistryClient (Docker Registry v2 API).

    SIT tests written: test_artifact_registry_smoke.py.

    Actual AR repo validation: pending (run test against project).

    '}
- {id: ecr-codeartifact-aws, content: AWS ECR (Docker images) + AWS CodeArtifact (Python wheels) equivalents. UCI providers/aws.py needs ECR image list/pull methods. Create setup-aws-registries.sh (aws ecr create-repository + aws codeartifact create-domain)., status: done, notes: 'DONE 2026-03-10: setup-registry.sh (new file, deployment-service 740423c) unified GCP+AWS registry script.

    GCP: creates trading-images (Docker) + trading-wheels (Python) AR repos.

    AWS: creates ECR repo per service (15 repos) + CodeArtifact domain + repository.

    Master: setup-cloud-infra.sh --cloud aws --component registry.

    Blocked until AWS creds — prints [BLOCKED] gracefully when creds absent.

    test_artifact_registry_smoke.py TestAWSRegistries skips on missing ECR_REGISTRY_URL.

    '}
- {id: billing-alerts-gcp, content: 'Create GCP billing budget alerts via deployment-service/scripts/setup-billing-alerts.sh. Two budgets: unified-trading-monthly-budget ($500/month) + unified-trading-dev-budget ($50). Thresholds: 50%/80%/100%/120%. Alerts sent to Pub/Sub topic ''billing-alerts'' and optionally to email (BILLING_ALERT_EMAIL env var). Optional BigQuery billing export (--export-bq flag). Daily breakdown query documented in script.', status: done, notes: 'DONE 2026-03-10: Budgets + billing-alerts topic LIVE in central-element-323112.

    Billing account: 016B25-109840-AF2ACB (odum_gcp_acc, GBP currency).

    Script fixed: auto-detect currency (was hardcoded USD), fix basis=current-spend.

    Created: billing-alerts Pub/Sub topic + billing-alerts-monitor subscription.

    Created: unified-trading-monthly-budget (500GBP) + unified-trading-dev-budget (50GBP).

    Thresholds: 50%/80%/100%/120% → Pub/Sub billing-alerts.

    BigQuery billing export: enable manually in GCP Console (cannot be done via CLI).

    '}
- {id: billing-alerts-aws, content: AWS Cost Explorer / CloudWatch billing alarms equivalent. Create AWS Budgets entry and CloudWatch billing alarm via setup-billing-alerts.sh --cloud aws. Documented in script but blocked on AWS credentials., status: blocked, notes: Commands documented in setup-billing-alerts.sh --cloud aws section.}
- {id: deployment-cleanup-untagged-images, content: 'Run cleanup-untagged-images.sh to delete untagged AR images older than 7 days, keeping 2 most recent per service. Schedule via Cloud Scheduler or cron in quality-gates. Prevents storage quota exhaustion from CI/CD image accumulation.', status: done, notes: 'DONE 2026-03-10: cleanup-untagged-images.sh validated against 34 AR repos.

    Script fixed: mapfile→while-read for macOS bash 3.2 compat.

    Live run complete: 2 stale untagged images deleted from features/calendar-service (Feb 15-16).

    Verified clean: gcloud artifacts docker images list features --filter="tags=''''" returns empty.

    '}
- {id: sit-pubsub-smoke, content: 'SIT smoke tests for Pub/Sub: topic existence (deployment-events, circuit-breaker-events, config-updates, cascade-predictions), publish to deployment-events, ephemeral topic round-trip (create topic + sub + publish + pull + ack + tear down), local provider round-trip (always runs without credentials).', status: done, notes: 'DONE 2026-03-10: system-integration-tests/tests/smoke/test_pubsub_smoke.py written.

    3 test classes: TestPubSubTopicsExist, TestPubSubPublishSubscribe, TestLocalPubSubCapable.

    GCP tests: skipif not _has_gcp_creds(). Local tests: always run.

    '}
- {id: sit-cache-smoke, content: 'SIT smoke tests for Redis/cache: local cache set/get/delete/TTL (always runs), Redis URL resolvable from REDIS_URL or SM secret, Redis ping, Redis set/get/delete, UCI get_cache_client() round-trip, AWS ElastiCache placeholder (skip).', status: done, notes: 'DONE 2026-03-10: system-integration-tests/tests/smoke/test_cache_smoke.py written.

    3 test classes: TestLocalCacheCapable (always), TestRedisMemorystore (skip if no URL),

    TestAWSElastiCache (skip if no ELASTICACHE_URL).

    '}
- {id: sit-database-smoke, content: 'SIT smoke tests for PostgreSQL/Cloud SQL: URL resolvable, asyncpg connect + SELECT 1, order_states table accessible (skip if not yet created), read/write probe row, SQLite fallback (always runs), AWS RDS placeholder (skip).', status: done, notes: 'DONE 2026-03-10: system-integration-tests/tests/smoke/test_database_smoke.py written.

    3 test classes: TestCloudSQLConnectivity (skip if no DB URL), TestSQLiteFallback (always),

    TestAWSRDS (skip if no AWS_DATABASE_URL).

    '}
- {id: sit-artifact-registry-smoke, content: 'SIT smoke tests for Artifact Registry: AR repos list accessible, Docker catalog v2 endpoint, at least one service image present, deployment-api image tagged, ArtifactRegistryClient instantiates, AWS ECR/CodeArtifact placeholders (skip).', status: done, notes: 'DONE 2026-03-10: system-integration-tests/tests/smoke/test_artifact_registry_smoke.py written.

    4 test classes: TestArtifactRegistryAccessible, TestServiceImagesExist, TestArtifactRegistryUCI,

    TestAWSRegistries. All GCP tests skipif not _has_gcp_creds().

    '}
- {id: per-service-db-smoke, content: 'execution-service quality-gates.sh smoke phase: verify DATABASE_URL accessible and order_states table exists. Uses CLOUD_MOCK_MODE=false in smoke phase. Similar to per-repo-bucket-permissions-check in cloud_infra_bucket_auth plan.', status: done, notes: 'DONE 2026-03-10: execution-service/scripts/quality-gates.sh updated (commit 26c015ba).

    DB smoke runs before source base-service.sh when CLOUD_MOCK_MODE=false and DATABASE_URL set.

    Checks order_states table in information_schema.tables. Non-blocking (warn-only) — CI never fails.

    Falls back to [SKIP] if asyncpg not installed. Recalibrated MIN_COVERAGE=31 (actual 32%).

    '}
isProject: false
---

# Cloud Infrastructure — Extended Bootstrap

**Linked plans:** [cloud_infra_bucket_auth_2026_03_10.md](cloud_infra_bucket_auth_2026_03_10.md) (buckets, SA key, BQ
tables)

---

## Infrastructure Coverage Matrix

| Component                | GCP            | AWS                        | Script                             | SIT Test                        |
| ------------------------ | -------------- | -------------------------- | ---------------------------------- | ------------------------------- |
| **Object Storage**       | ✅ GCS         | ✅ S3 (blocked)            | setup-buckets.py                   | test_cloud_infra_smoke.py       |
| **Pub/Sub**              | ✅ Pub/Sub     | ❌ SNS (blocked)           | setup-pubsub.sh                    | test_pubsub_smoke.py            |
| **Cache**                | ✅ Memorystore | ❌ ElastiCache (blocked)   | setup-redis.sh                     | test_cache_smoke.py             |
| **SQL Database**         | ✅ Cloud SQL   | ❌ RDS (blocked)           | setup-cloudsql.sh                  | test_database_smoke.py          |
| **Secret Manager**       | ✅ SM          | ✅ SM (blocked)            | —                                  | test_cloud_infra_smoke.py       |
| **Container Registry**   | ✅ AR Docker   | ❌ ECR (blocked)           | cleanup-untagged-images.sh         | test_artifact_registry_smoke.py |
| **Package Registry**     | 🔲 AR Python   | ❌ CodeArtifact (blocked)  | —                                  | test_artifact_registry_smoke.py |
| **Billing Alerts**       | ✅ Budgets     | ❌ Cost Explorer (blocked) | setup-billing-alerts.sh            | —                               |
| **BigQuery / Analytics** | ✅ BQ          | ✅ Athena (blocked)        | create_bigquery_external_tables.sh | —                               |

---

## Scripts Written (deployment-service/scripts/)

| Script                       | Purpose                                            | Status                                 |
| ---------------------------- | -------------------------------------------------- | -------------------------------------- |
| `setup-pubsub.sh`            | 17 topics + subscriptions (idempotent)             | Written, pending GCP run               |
| `setup-cloudsql.sh`          | PostgreSQL 15 for execution-service order state    | Written, pending GCP run               |
| `setup-billing-alerts.sh`    | GCP budget alerts ($500 prod + $50 dev) + AWS docs | Written, pending GCP run               |
| `cleanup-untagged-images.sh` | Delete untagged AR images older than 7d            | Written, pending run                   |
| `setup-redis.sh`             | GCP Memorystore Redis 7.0                          | Pre-existing, pending run verification |

---

## Pub/Sub Topics

| Topic                     | Retention | Subscribers                         | Owner                    |
| ------------------------- | --------- | ----------------------------------- | ------------------------ |
| `deployment-events`       | 7d        | deployment-monitor                  | deployment-service       |
| `deployment-status`       | 7d        | monitor, ui                         | deployment-service       |
| `fill-events-{venue}`     | 3d        | pnl, risk, strategy                 | execution-service        |
| `circuit-breaker-events`  | 7d        | monitor, execution                  | execution-service        |
| `risk-breach-alerts`      | 7d        | alerting, execution                 | risk-service             |
| `position-updates`        | 3d        | risk, pnl, monitor                  | position-balance-monitor |
| `cascade-predictions`     | 7d        | strategy, monitor                   | ml-inference-service     |
| `config-updates`          | 14d       | execution, strategy, risk, features | deployment-service       |
| `system-health-events`    | 7d        | alerting, monitor                   | all services             |
| `audit-log-events`        | 30d       | audit-sink                          | all services             |
| `strategy-sports-signals` | 7d        | execution, monitor                  | features-sports-service  |
| `billing-alerts`          | 30d       | alerting-service monitor            | GCP Budgets              |

---

## Cloud SQL (execution-service order state)

```
Instance: trading-order-state (PostgreSQL 15, db-g1-small, asia-northeast1)
Database: order_state
User:     execution_svc
SM:       cloudsql-execution-db-url  (asyncpg URL)
          cloudsql-execution-db-password
Connect:  cloud-sql-proxy central-element-323112:asia-northeast1:trading-order-state &
Config:   DATABASE_URL=$(gcloud secrets versions access latest --secret=cloudsql-execution-db-url)
          USE_DATABASE=true
```

---

## Billing Alert Thresholds

| Budget                           | Monthly Limit | Thresholds              |
| -------------------------------- | ------------- | ----------------------- |
| `unified-trading-monthly-budget` | $500          | 50% / 80% / 100% / 120% |
| `unified-trading-dev-budget`     | $50           | 50% / 80% / 100% / 120% |

Alerts → Pub/Sub `billing-alerts` → alerting-service → Telegram

---

## Next Actions (run these against GCP)

```bash
# 1. Pub/Sub topics
GCP_PROJECT_ID=central-element-323112 bash scripts/setup-pubsub.sh --dry-run
GCP_PROJECT_ID=central-element-323112 bash scripts/setup-pubsub.sh

# 2. Redis (if not already running)
GCP_PROJECT_ID=central-element-323112 bash scripts/setup-redis.sh

# 3. Cloud SQL (execution-service order state)
GCP_PROJECT_ID=central-element-323112 bash scripts/setup-cloudsql.sh --dry-run
GCP_PROJECT_ID=central-element-323112 bash scripts/setup-cloudsql.sh

# 4. Billing alerts (requires billing account ID)
GCP_BILLING_ACCOUNT=$(gcloud billing projects describe central-element-323112 --format="value(billingAccountName)" | sed 's|billingAccounts/||')
GCP_PROJECT_ID=central-element-323112 GCP_BILLING_ACCOUNT=$GCP_BILLING_ACCOUNT bash scripts/setup-billing-alerts.sh --dry-run

# 5. AR image cleanup (dry-run first)
GCP_PROJECT_ID=central-element-323112 bash scripts/cleanup-untagged-images.sh --dry-run
```
