---
scope: [engineer, admin]
title: Cloud-Agnostic Audit (point-in-time 2026-05-07)
status: planned
created: 2026-05-07
authoritative_for:
  Workspace-wide audit (snapshot 2026-05-07) of every shell script + every Python script + every Cloud Run service +
  every adapter against the cloud-agnostic-script-pattern. Tracks compliance status + per-violation remediation owner +
  target completion date.
referenced_by:
  - plans/active/aws_migration_defi_first_2026_05_07.md
related:
  - codex/05-infrastructure/cloud-agnostic-script-pattern.md
  - codex/05-infrastructure/cloud-agnostic-build-lineage.md
last_reviewed: 2026-05-17
---

# Cloud-Agnostic Audit (2026-05-07)

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from active plans. Body to be filled in as
> the audit completes; this is the punch list that drives the AWS migration.

> **🟡 IN-FLIGHT REFACTOR — operator decision (b+) 2026-05-11.** The bucket-naming SSOT operator decision (per
> [`plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`](../../plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md)
> Phase 0a) extends the env-tier convention from yaml's Group-B-only (features-\* / ml-\* / strategy-\* / execution-\*)
> to **ALL buckets** (raw-tick / instruments-store / manifest / etc.) across BOTH clouds × 3 envs
> (staging/prod/development). Adds a prod → staging/dev sync script with truncated date window (1-2 yrs) + same-region
> enforcement + env-aware VM launcher scripts. Audit findings post-2026-05-11 must classify violations against the (b+)
> target shape, not the (a) drop-env-tier shape.

## Purpose

Snapshot the workspace's compliance with [`cloud-agnostic-script-pattern`](./cloud-agnostic-script-pattern.md) on
2026-05-07, file-by-file. Each violation gets a remediation row (file, violation kind, owner, target date) so the AWS
migration plan has a concrete punch list rather than "we'll find them as we go."

## Scope

- All `*.sh` files under any repo's `scripts/` directory.
- All `*.py` files importing `google.cloud.*`, `boto3`, or shelling out to `gcloud`/`aws`/`gsutil`.
- All Cloud Run services' Dockerfiles + entrypoints.
- All `Dockerfile`s with cloud-specific base image references.
- Excluded: PM repo (docs only), `.venv*`, `node_modules/`, generated SVG/DAG artefacts.

## Outline (planned sections)

1. **Audit methodology** — the rg invocation, the AST walker for Python imports, the manual review for false-positives.
2. **Violation taxonomy** — `HARDCODED_GCLOUD`, `HARDCODED_GSUTIL`, `DIRECT_GOOGLE_CLOUD_IMPORT`, `MISSING_CLOUD_FLAG`,
   `HARDCODED_BUCKET_PREFIX`, `MIXED_CLOUD_NO_BRANCH`.
3. **Audit table** — one row per violation: `file:line, violation_kind, snippet, severity, owner, target_date, status`.
4. **Per-repo summary** — aggregate compliance % per repo; identify the 5 repos with the most work.
5. **Remediation roadmap** — phased fix plan; quick wins (mechanical) vs heavy lifts (services that need UCI plumbing).
6. **Re-audit cadence** — quarterly re-run + diff against this baseline; new violations get filed automatically by QG.

## Cross-references

- **Plan(s) implementing this:**
  [`aws_migration_defi_first`](../../plans/active/aws_migration_defi_first_2026_05_07.md).
- **Related codex SSOTs:** [`cloud-agnostic-script-pattern`](./cloud-agnostic-script-pattern.md),
  [`cloud-agnostic-build-lineage`](./cloud-agnostic-build-lineage.md).
- **Code:** TBD audit script — likely `unified-trading-pm/scripts/audit/cloud-agnostic-audit.sh`.

## Open questions

- Where does the audit-table data live — a separate `.parquet`, a checked-in `.yaml`, or just a markdown table that the
  audit script regenerates?
- How do we count "violation severity" — number of call sites, frequency of execution, blast radius if it breaks at
  cutover?
- Do we hard-block PRs that introduce new violations, or just track them with an SLA?
- Who owns the audit re-run — workspace-wide infrastructure rotation, or assigned per-repo?

## Inline-string bucket-name audit (2026-05-08)

First-pass enumeration ahead of the Tab 4 (AWS migration) bucket-naming SSOT consolidation (UTL@`780a9575` shipped
`cloud_interface/bucket_naming.py` as the canonical resolver). Findings populate the audit table once methodology lands;
for now they're a punch-list for Wave 2 (consumer migration sweep).

### 1. `gs://` literals + `central-element-323112` project-id hardcodes

`grep -rn "central-element-323112\\|gs://" --include="*.py" --include="*.sh"` from `WORKSPACE_ROOT` (excluding `.venv*`,
`archive/`, `_archived/`, `node_modules/`, `build/`, `dist/`): ~1961 hits across 80+ files. Classification:

| Category                                                                                          | Count     | Action                                                               |
| ------------------------------------------------------------------------------------------------- | --------- | -------------------------------------------------------------------- |
| (a) UCI-resolved (lookup via `cloud_interface.factory` or new `bucket_naming.resolve_bucket_uri`) | ~95%      | Compliant — no action.                                               |
| (b) Test fixtures using SSOT-correct shape                                                        | ~3%       | Compliant — no action.                                               |
| (c) Legacy `# noqa: gs-uri` markers (already triaged, awaiting Wave 2 sweep)                      | ~85 sites | Wave 2 — migrate to `resolve_bucket_uri`.                            |
| (d) Untriaged `f"gs://"` / `f"s3://"` formatting (real anti-pattern)                              | ~70 sites | Wave 2 P0 — migrate.                                                 |
| (e) Module-level `BUCKET = "..."` constants                                                       | ~30 sites | Wave 2 P1 — migrate to lazy lookup.                                  |
| (f) Operator-run one-off migration scripts (`scripts/migrate_*.py`)                               | small set | Compliant exception per "scripts excluded from Tier-3 default" rule. |

Hot-spot: `strategy-service/strategy_service/storage/gcs_storage_service.py` — 8+ inline `f"gs://"` sites, all
`# noqa: gs-uri`-marked. Single-file refactor target once `bucket_naming.py` ships (now done).

UTL-internal anti-pattern fix shipped 2026-05-08: `unified-trading-library/unified_trading_library/core/seed_writer.py`
(lines 167/180/192/204 previously built `f"gs://{self._bucket}/{blob}"` directly) now routes through `_format_uri()`
cached at `__init__` via `get_cloud_provider()`. UTL@`780a9575`.

### 2. `cloud-providers.yaml` GCP↔AWS parity check

Probed `deployment-service/configs/cloud-providers.yaml`: every key under `gcp.storage.*` has a matching key under
`aws.storage.*`. **24 keys, zero drift.** Phase 2 (deployment-service@`7da2f3d`) closed the 10 documented gaps
(`dex-pools`, `dex-swaps`, `evm-defi`, `eigenlayer-rewards`, `solana-defi`, `pnl-store-defi`, `positions-store-defi`,
`risk-store-defi`, `events`, `config-store`). Yaml-side parity is **DONE** for the AWS plan Phase 1.5.A yaml-parity
sub-item.

### 3. Bucket-name SUFFIX drift

GCS pattern: `<kind>-central-element-323112-<asset_group>` — asset_group as **suffix** (e.g.
`pnl-store-central-element-323112-defi`).

AWS template: `unified-trading-<kind>-<asset_group>-<env>-<account>` — asset_group as **infix** (e.g.
`unified-trading-pnl-store-defi-prod-427895769566`).

**Recommendation: keep both, hide asymmetry behind `resolve_bucket_name`.** The yaml internally maps each `kind` to
per-cloud templates; same lookup-key works for both. Migrating GCS bucket data on disk to match AWS-style infix is
prohibitively expensive (PB-scale rename) and gives nothing — the resolver abstracts the difference. Wave 2 sweep
migrates code from inline strings to the resolver; on-disk data stays put.

### 4. Companion follow-ups (out of scope for 2026-05-08)

- `cloud_interface/constants.py:BUCKET_PREFIXES` is a drifted hardcode that pre-dates the yaml SSOT — missing several
  recently-added kinds (`dex-pools`, `events`, `config-store`, etc.). Migrate `constants.get_bucket_name()` to delegate
  into `bucket_naming.resolve_bucket_name()` (deprecate the hardcode).
- `UnifiedCloudConfig.<kind>_<cloud>_bucket_<asset_group>` fields (per-field env-var overrides) compose with
  `bucket_naming` rather than replace it — document the layering in `cloud-agnostic-script-pattern.md` § "Authentication
  (5)" extension if this layering surfaces a footgun.

### 5. AWS Phase 1 smoke readiness (2026-05-08)

Code-path readiness for `CLOUD_PROVIDER=aws` runtime swing: **🟢 GREEN.** Factory swings cleanly between
`GCSStorageClient` and `S3StorageClient`; AWS provider methods at parity with GCS for read/write/list/exists/delete/copy
on the `StorageClient` ABC; `boto3` is a flat dep (`>=1.40.70`); production services route through the factory rather
than direct `google.cloud.storage` imports.

End-to-end Phase 1 smoke readiness: **🟡 AMBER.** Bucket-naming triple-drift between (a) `setup-defi-buckets.sh`
provisioned shape, (b) `BUCKET_PREFIXES` hardcode in `cloud_interface/constants.py`, (c) `UnifiedCloudConfig` per-field
env-var defaults — none of the three agree on `(market_data, defi)` target bucket. Phase 1 smoke ships TODAY with
band-aid (`MARKET_DATA_S3_BUCKET_DEFI` env explicit override), but Citadel-grade SSOT alignment requires the operator
triage call captured in
[`plans/active/issues/aws_phase_1_smoke_blockers_2026_05_08.md`](../../plans/archive/issues/aws_phase_1_smoke_blockers_2026_05_08.md).

### 6. AWS hardcode enumeration (2026-05-22)

`grep -rn "unified-trading-\|s3://\|427895769566" --include="*.py" --include="*.sh"` across all service repos (excluding
`.git`, `.venv*`, `__pycache__`). ~200 hits total. Classification:

| Category                                                                                         | Example sites                                                                                                                                                                                        | Count   | Action                                                                           |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | -------------------------------------------------------------------------------- |
| (a) Multi-cloud-aware dispatch (handles both `gs://` + `s3://` explicitly)                       | `deployment-api/routes/services.py`, `deployment-service/cloud_client.py`, `setup-buckets.py`, `sync-buckets-prod-to-env.sh`                                                                         | ~80     | Compliant — no action.                                                           |
| (b) Test fixtures using SSOT-correct shape                                                       | `deployment-api/tests/unit/test_data_status_hierarchical_aws_path.py`, `execution-service/tests/unit/custody/test_cloud_kms_provider.py`, `strategy-service/tests/unit/test_cloud_agnostic_paths.py` | ~60     | Compliant — no action.                                                           |
| (c) Operator migration + audit scripts (`unified-trading-pm/scripts/migration/`, `plans/audit/`) | `verify_env_tiered_buckets_provisioned.py:56` (`_DEFAULT_AWS_ACCOUNT_ID = "427895769566"`), `a3v2_manifest_divergence_all_services.py:74`                                                            | ~20     | Compliant exception (scripts excluded from Tier-3 rule).                         |
| (d) Env-var-driven AWS backends with `${AWS_REGION:-us-east-1}` fallback                         | `deployment-service/deployment_service/config_loader.py:524,582-583` (ECR URL construction uses `substitute_env_vars`)                                                                               | ~10     | Compliant — env-var pattern correct.                                             |
| (e) **Wave 2**: bare `us-east-1` region hardcodes in deployment-api command strings              | `deployment-api/deployment_api/routes/monitor_scheduled.py:327,422,460`; `monitor_live.py:54` (`_DEFAULT_ECS_REGION = "us-east-1"`)                                                                  | 4 sites | Post-cutover — deployment-api scope. Fix: read from `AWS_REGION` env via config. |
| (f) QG + quality-gate scripts (the enforcers, not violations)                                    | `scripts/quality_gates/check_inline_bucket_uri.py`, `scripts/quality-gates-base/base-service.sh` STEP 5.12b                                                                                          | ~30     | Compliant — these ARE the detection layer.                                       |

**Overall finding: ZERO violations in the May-23 critical path.** All `s3://` and `427895769566` hits in production
service code are either multi-cloud-aware dispatch (category a) or env-var-driven (category d).

**Wave 2 items** (post-cutover, deployment-api scope):

- `deployment-api/deployment_api/routes/monitor_scheduled.py:327` — `f"'cron(...)' --region us-east-1"` in EventBridge
  schedule command. Fix: `AWS_DEFAULT_REGION` env or deployment-api config field.
- `deployment-api/deployment_api/routes/monitor_scheduled.py:422,460` —
  `aws events disable-rule --name {name} --region us-east-1` + enable-rule. Same fix.
- `deployment-api/deployment_api/routes/monitor_live.py:54` — `_DEFAULT_ECS_REGION = "us-east-1"` module-level constant.
  Fix: read from `AWS_DEFAULT_REGION` env.
- `deployment-api/deployment_api/deployment_api_config.py:562` — valid-regions list
  `["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]` (config enum). Acceptable: it's a validation whitelist,
  not a routing decision.

**`unified-trading-` prefix hits**: All from `unified-trading-pm` repo name in comments/docstrings, NOT inline bucket
name strings. QG STEP 5.12b (`grep '"gs://\|"s3://'`) already enforces the bucket-literal ban in service code. Zero new
anti-patterns found.

### 7. GCP Pub/Sub topic + subscription inventory (2026-05-23)

Per `aws_migration_defi_first_2026_05_07.md` Phase 1.5.B — inventory of GCP Pub/Sub topics for SNS+SQS parity.

**Static inventory method**: `gcloud pubsub topics list --project central-element-323112` not available from AWS VM (no
gcloud CLI or ADC credentials). Topics enumerated via static code analysis:

- `unified_api_contracts/internal/event_topics.py` — canonical EVENT_TOPIC_REGISTRY (18 topics, inter-service domain
  events)
- `unified_trading_library/config_reloader.py` — config/lifecycle infrastructure topics
- `unified_trading_library/service_framework/_sink_factory.py` — service-level event sink topics
- `unified-trading-pm/scripts/dev/setup-dev-pubsub.sh` — dev environment topic templates (RETIRED 2026-03-13; canonical
  source is now Terraform in deployment-service)

**BLOCKED-OPERATOR**: live `gcloud pubsub topics list` output from `central-element-323112` is needed to confirm no
additional ad-hoc topics exist. Operator to run from GCP-authenticated machine:

```bash
gcloud pubsub topics list --project central-element-323112 --format="value(name)" | sort
gcloud pubsub subscriptions list --project central-element-323112 --format="table(name,topic)" | sort
```

and append results as section 7.A below.

#### 7.A — Statically enumerated topics (non-test, production code)

**Inter-service domain events** (from `unified_api_contracts/internal/event_topics.py`):

| GCP topic                  | Producer                         | Key consumers                                                                                             | Retention |
| -------------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------- | --------- |
| `alert-dispatched`         | alerting-service                 | risk-and-exposure-service, strategy-service                                                               | 7d        |
| `balance-snapshots`        | position-balance-monitor-service | strategy-service, risk-and-exposure-service                                                               | 7d        |
| `deleverage-actions`       | risk-and-exposure-service        | execution-service                                                                                         | 7d        |
| `fill-events`              | execution-service                | position-balance-monitor-service, pnl-attribution-service                                                 | 7d        |
| `kill-switch-triggers`     | alerting-service                 | execution-service, strategy-service                                                                       | 7d        |
| `liquidation-alerts`       | position-balance-monitor-service | alerting-service, pnl-attribution-service, risk-and-exposure-service                                      | 30d       |
| `margin-events`            | position-balance-monitor-service | alerting-service, risk-and-exposure-service, strategy-service, execution-service, pnl-attribution-service | 14d       |
| `order-events`             | execution-service                | position-balance-monitor-service, pnl-attribution-service                                                 | 7d        |
| `pnl-attribution`          | pnl-attribution-service          | strategy-service, risk-and-exposure-service                                                               | 7d        |
| `pnl-points`               | pnl-attribution-service          | strategy-service                                                                                          | 7d        |
| `position-snapshots`       | position-balance-monitor-service | strategy-service, risk-and-exposure-service                                                               | 7d        |
| `price-snapshots`          | position-balance-monitor-service | strategy-service                                                                                          | 7d        |
| `reconciliation-completed` | risk-and-exposure-service        | alerting-service, pnl-attribution-service                                                                 | 7d        |
| `reconciliation-deviation` | risk-and-exposure-service        | alerting-service                                                                                          | 7d        |
| `risk-events`              | risk-and-exposure-service        | alerting-service, strategy-service, execution-service                                                     | 7d        |
| `shadow-comparison`        | risk-and-exposure-service        | alerting-service                                                                                          | 7d        |
| `strategy-instructions`    | strategy-service                 | execution-service                                                                                         | 7d        |
| `strategy-signals`         | strategy-service                 | strategy-service (self), execution-service                                                                | 7d        |

**Infrastructure / config topics** (from UTL `config_reloader.py` + `domain_config_reloader.py`):

| GCP topic                | Purpose                                                                    | Pattern   |
| ------------------------ | -------------------------------------------------------------------------- | --------- |
| `config-updates`         | Global service config hot-reload (UTL `ConfigReloader`)                    | static    |
| `config-domain-{domain}` | Per-domain config reload (e.g. `config-domain-defi`, `config-domain-cefi`) | templated |
| `lifecycle-events`       | Service STARTED/STOPPED/FAILED events                                      | static    |
| `{service-name}-events`  | Per-service event sink (UTL `_sink_factory` live mode default)             | templated |

**Service pipeline topics** (from dev script templates; Terraform-provisioned in production):

| Topic pattern                            | Owner service                     | Fan-out                                                   |
| ---------------------------------------- | --------------------------------- | --------------------------------------------------------- |
| `instrument-events-{venue}`              | instruments-service               | market-tick-data-service, features-\*                     |
| `raw-ticks-{venue}-{itype}-{dtype}`      | market-tick-data-service          | market-data-processing-service, features-\*               |
| `processed-candles-{venue}-{itype}-{tf}` | market-data-processing-service    | features-delta-one-service, features-volatility-service   |
| `features-delta-one-{fc}-{venue}`        | features-delta-one-service        | strategy-service, ml-inference-service                    |
| `features-volatility-{fc}-{venue}`       | features-volatility-service       | strategy-service, ml-inference-service                    |
| `features-cross-instrument-{fc}`         | features-cross-instrument-service | strategy-service                                          |
| `ml-predictions-{venue}`                 | ml-inference-service              | strategy-service                                          |
| `execution-orders`                       | execution-service                 | position-balance-monitor-service                          |
| `execution-fills`                        | execution-service                 | position-balance-monitor-service, pnl-attribution-service |
| `circuit-breaker-events`                 | execution-service                 | alerting-service, risk-and-exposure-service               |
| `system-alerts`                          | alerting-service                  | operator notification channels                            |

#### 7.B — AWS SNS+SQS routing policy

**Policy rule**: Use **SNS+SQS** for all trading-event, domain-event, and command topics. Use **EventBridge** only for
deployment-orchestration where cross-account CodePipeline routing is required.

**Trade-off**: SNS doesn't natively dedup; SQS visibility-timeout provides at-least-once semantics acceptable for all
trading topics (duplicate alerts/commands handled idempotently by consumers).

**AWS naming convention**: `uts-{gcp-topic-name}` (e.g. GCP `margin-events` → AWS SNS `uts-margin-events` + SQS
`uts-margin-events-{consumer-service}`). Follows the `unified-trading-` prefix convention established in section 3.

**Provisioning**: `deployment-service/scripts/aws/setup-messaging.sh` (not yet written — tracked as Phase 1.5.B item 5
in `aws_migration_defi_first_2026_05_07.md`) should create SNS topics + SQS queues for all 18 domain-event topics +
infrastructure topics. Per-venue/instrument-type/timeframe pipeline topics (~100+ topics) are provisioned by the
per-service launch scripts at VM startup.

### 8. gcloud storage / gsutil / google.cloud.storage audit (2026-05-23)

Phase 1.5.D audit — `grep -rln "gcloud storage\|gsutil\|google.cloud.storage"` across available workspace repos (UTL +
UAC + agent-orchestrator + PM). **32 files total.** Service repos not in worktree (Wave 2).

| Category                            | Files                                                                                                                                                              | Action                                                                                                                                                                                                                       |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GCP provider layer (correct)        | `UTL/providers/gcp.py`, `UTL/gcs_blob_ops.py`, `UTL/presigned_urls.py`, `UAC/external/gcp/gcs.py`, `UAC/external/gcp/protocols.py`, `UAC/external/gcp/firebase.py` | Compliant — GCP APIs belong in GCP provider implementation                                                                                                                                                                   |
| UTL production code — comments only | `manifest_consolidator.py`, `domain_client/artifact_store.py`, `io/streaming_writer.py`                                                                            | Compliant — "google.cloud.storage" only in docstrings/comments, not in imports or code                                                                                                                                       |
| Operator setup + migration scripts  | `PM/scripts/setup.sh`, `UAC/scripts/setup.sh`, `PM/scripts/migration/*.py`, `PM/scripts/orchestrator/push_creds_to_gcs.sh`                                         | Exempt per Tier-3 operator script rule                                                                                                                                                                                       |
| Dev tools                           | `PM/scripts/dev/*.sh`, `PM/scripts/workspace/check-import-deps.py`, `PM/scripts/openapi/*.py`                                                                      | Exempt — dev environment tools                                                                                                                                                                                               |
| UAC internal testing seeds          | `seed_features.py:327`, `seed_ml_artifacts.py:258,260`                                                                                                             | Log messages with gsutil guidance for developers; not actual gsutil imports or invocations                                                                                                                                   |
| Agent-orchestrator                  | `scripts/restore_from_gcs.sh` (gsutil ls/cp), `server/oauth_refresh.py`, `scripts/bootstrap_vm.sh`                                                                 | `bootstrap_vm.sh` has CLOUD_PROVIDER toggle ✅. `restore_from_gcs.sh` is GCP-only recovery tool — needs `--cloud` flag as Wave 2. `oauth_refresh.py` is GCP auth only — acceptable for orchestrator VM credential management |
| Tests                               | `tests/cloud_interface/conftest.py`, `test_gcp_secret_storage_build.py`                                                                                            | Compliant — GCP-specific test fixtures                                                                                                                                                                                       |

**Finding: ZERO violations in May-23 critical path** across all 4 available repos. Service-repo scripts
(deployment-service `launch-*.sh`, instruments-service reconcilers, etc.) are Wave 2 post-cutover — Phase 9 scope per
plan note "Phase 9 ships per-asset-group AWS launcher equivalents."
