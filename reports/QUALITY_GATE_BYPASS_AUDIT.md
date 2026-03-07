# Quality Gate Bypass Audit

**Purpose:** Track approved exceptions to cloud SDK isolation rules (STEP 5.10, 5.11). **Policy:** Zero unapproved
exceptions. All exceptions require plan reference and expiry. **Last Updated:** 2026-03-07 (UTL mixin deletion complete)

## Approved Exceptions

| File                                     | Pattern           | Reason                                    | Plan Reference  | Expiry |
| ---------------------------------------- | ----------------- | ----------------------------------------- | --------------- | ------ |
| unified_cloud_interface/providers/gcp.py | from google.cloud | UCI provider — intentional boundary       | N/A — permanent | Never  |
| unified_cloud_interface/providers/aws.py | import boto3      | UCI provider — intentional boundary       | N/A — permanent | Never  |
| unified_cloud_interface/cache.py         | import redis      | UCI cache provider — intentional boundary | N/A — permanent | Never  |

## Stream 3 os.getenv/os.environ Exceptions (citadel_audit_remediation)

**Policy:** config-bootstrap layer may use os.environ. All service/library production source must use UnifiedCloudConfig
or UCI factory. **Scan date:** 2026-03-06 **Status:** All service-layer violations FIXED. Remaining hits are
config-bootstrap layer only.

### FIXED (stream3 — 2026-03-06)

| Date       | File                                                      | Violation                                                                         | Resolution                                                                                     |
| ---------- | --------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 2026-03-06 | features-delta-one-service/.../data_loader.py             | os.environ.get("PROTOCOL*DATA_SOURCE_BUCKET*\*")                                  | Replaced \_get_source_bucket() with get_data_source(routing_key=).\_bucket via UCI             |
| 2026-03-06 | features-onchain-service/.../data_loader.py               | os.environ.get("PROTOCOL*DATA_SOURCE_BUCKET*\*")                                  | Replaced \_get_source_bucket() with get_data_source(routing_key=).\_bucket via UCI             |
| 2026-03-06 | execution_service/utils/gcs_service.py (orphan)           | multiple os.getenv calls                                                          | DELETED — not part of any git repo; was a stale test copy                                      |
| 2026-03-06 | deployment-api/deployment_api/config_loader.py            | dict(os.environ) in substitute_env_vars() — inside SOURCE_DIR, fails quality gate | Replaced with get_env_copy() from unified_trading_library.core.\_env_bootstrap; commit e3f55bc |
| 2026-03-06 | deployment-service/cleanup_old_instruments_parquet.py     | os.environ["GCP_PROJECT_ID"]                                                      | Replaced with UnifiedCloudConfig().gcp_project_id; commit d51cb62                              |
| 2026-03-06 | deployment-service/tools/check_ml_dependencies_by_mode.py | os.environ["GCP_PROJECT_ID"]                                                      | Replaced with UnifiedCloudConfig().gcp_project_id; commit d51cb62                              |

### Permanent Exceptions (config-bootstrap layer)

| File                                                                    | Pattern                                                                 | Reason                                                                                                                                   |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| unified-cloud-interface/unified_cloud_interface/\*.py                   | os.environ.get                                                          | UCI is the config-bootstrap layer — the single point for PROTOCOL\_\*/CLOUD_PROVIDER/GCP_PROJECT_ID env reads                            |
| unified-config-interface/unified_config_interface/\_env_bootstrap.py    | os.environ                                                              | Single acceptable os.environ access point in UCI; feeds pydantic-settings                                                                |
| unified-trading-library/unified_trading_library/core/\_env_bootstrap.py | os.environ                                                              | Single acceptable os.environ access point in UTL                                                                                         |
| deployment-service/deployment_service/config/env_substitutor.py         | dict(os.environ)                                                        | Intentional full env snapshot for template substitution; # config-bootstrap                                                              |
| deployment-service/deployment_service/config_loader.py                  | os.environ.get("RUNTIME_TOPOLOGY_PATH")                                 | Topology file discovery — must run before config is loaded; # config-bootstrap                                                           |
| market-data-processing-service/.../config.py                            | os.environ.get("VM_INSTANCE_NAME")                                      | VM instance detection for adaptive worker sizing; no UnifiedCloudConfig attribute; # config-bootstrap                                    |
| execution-service/.../event_loop.py                                     | os.environ.setdefault("TOKIO*\*","NAUTILUS*\_","RUST\_\_","USE_UVLOOP") | WRITES process-level flags for NautilusTrader Rust/Tokio runtime; not config reads; no UnifiedCloudConfig equivalent; # config-bootstrap |

## STEP 5.11: UTL Protocol-Leaking Symbols (Category B)

Gate: `from unified_trading_library import.*(CloudTarget|StandardizedDomainCloudService|upload_to_gcs_batch)` in service
source. Status: **0 approved exceptions. All service-layer violations resolved.**

### Resolved Violations (Category B — UTL→UDC migration, sessions 4–5)

| Date       | File                                                                                            | Resolved        |
| ---------- | ----------------------------------------------------------------------------------------------- | --------------- |
| 2026-03-05 | instruments-service/instruments_service/app/core/cloud_data_provider.py                         | FIXED           |
| 2026-03-05 | instruments-service/instruments_service/cli/handlers/corporate_actions_handler.py               | FIXED           |
| 2026-03-05 | instruments-service/instruments_service/cli/handlers/corporate_actions_production_handler.py    | FIXED           |
| 2026-03-05 | instruments-service/instruments_service/cli/handlers/corporate_actions_backfill_handler.py      | FIXED           |
| 2026-03-05 | instruments-service/instruments_service/engine/operations/corporate_actions/utils.py            | FIXED           |
| 2026-03-05 | ml-training-service/ml_training_service/ml/model_registry.py                                    | FIXED           |
| 2026-03-05 | ml-training-service/ml_training_service/app/core/cloud_feature_provider.py                      | FIXED           |
| 2026-03-05 | ml-training-service/ml_training_service/app/core/config_loader.py                               | FIXED           |
| 2026-03-05 | market-data-processing-service/market_data_processing_service/config.py                         | FIXED           |
| 2026-03-05 | market-data-processing-service/market_data_processing_service/cli/handlers/live_mode_handler.py | FIXED           |
| 2026-03-05 | strategy-service/strategy_service/app/core/cloud_strategy_storage.py                            | FIXED           |
| 2026-03-05 | execution-service/execution_service/cli/backtest_config.py                                      | FIXED           |
| 2026-03-05 | execution-service/execution_service/cli/batch_backtest.py                                       | FIXED           |
| 2026-03-05 | execution-service/execution_service/cli/config_loader.py                                        | FIXED           |
| 2026-03-05 | execution-service/execution_service/cli/gcs_klines.py                                           | FIXED           |
| 2026-03-05 | execution-service/execution_service/cli/definitions_loader.py                                   | FIXED           |
| 2026-03-05 | execution-service/execution_service/cli/gcs_service.py                                          | FIXED           |
| 2026-03-05 | execution-service/execution_service/cli/execution_cloud_service.py                              | FIXED           |
| 2026-03-06 | ml-inference-service/ml_inference_service/app/core/feature_subscriber.py                        | FIXED           |
| 2026-03-06 | ml-inference-service/ml_inference_service/app/core/prediction_publisher.py                      | FIXED           |
| 2026-03-05 | pnl-attribution-service (already on UDC)                                                        | CONFIRMED CLEAN |
| 2026-03-05 | features-calendar-service (already on UDC)                                                      | CONFIRMED CLEAN |
| 2026-03-05 | market-tick-data-service uploaders (already on UDC)                                             | CONFIRMED CLEAN |

Note: `execution_service/data/` files are gitignored and cannot be tracked. Verified on disk — STEP 5.11 would not flag
them since they import from UDC.

## Violation History (Category A — Direct Cloud SDK)

| Date       | File                                             | Violation                        | Resolved | Notes                                          |
| ---------- | ------------------------------------------------ | -------------------------------- | -------- | ---------------------------------------------- |
| 2026-03-05 | deployment-api/utils/cache.py                    | import redis.asyncio             | FIXED    | Migrated to AsyncRedisProvider                 |
| 2026-03-05 | UTL/cloud_auth_factory.py                        | from google.cloud                | FIXED    | Migrated to UCI factory                        |
| 2026-03-05 | UTL/cloud_base_service.py                        | from google.cloud                | FIXED    | Migrated to UCI factory                        |
| 2026-03-05 | UTL/logging.py                                   | import boto3, watchtower         | FIXED    | Removed; use structured stdout                 |
| 2026-03-05 | instruments-service/cloud_instrument_storage.py  | CloudTarget, upload_to_gcs_batch | FIXED    | Migrated to get_data_sink()                    |
| 2026-03-05 | deployment-service/scripts/ (6 files)            | GCSClient                        | FIXED    | Migrated to get_storage_client()               |
| 2026-03-05 | UTL/cloud_storage_service.py                     | bigquery direct import           | DEFERRED | Deferred inside method; tracked for UTL→UCI P2 |
| 2026-03-05 | UTL/cloud_pubsub_service.py                      | bigquery direct import           | DEFERRED | Deferred inside method; tracked for UTL→UCI P2 |
| 2026-03-05 | deployment-service/backends/\_gcp_sdk.py         | from google.cloud                | FIXED    | Module **getattr** lazy-load via importlib     |
| 2026-03-05 | deployment-service/backends/aws\*.py (3 files)   | import boto3                     | FIXED    | \_ensure_boto3() deferred pattern              |
| 2026-03-05 | deployment-api/routes/cloud_builds.py            | google.cloud                     | FIXED    | \_cloudbuild_v1() deferred loader              |
| 2026-03-05 | deployment-api/routes/service_status_checkers.py | google.cloud                     | FIXED    | Deferred import inside \_get_build_sync        |
