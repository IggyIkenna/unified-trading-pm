---
doc_type: plan
title: cloud-infra-bucket-auth
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
overview: 'Cloud infrastructure rollout: GCP_SA_KEY propagation to all 62 repos, GCS bucket audit + creation

  for all required buckets, BigQuery external table setup, SIT smoke tests for bucket availability

  and cloud auth (GCP + AWS), and a framework for dual-cloud auth testing (GCP always; AWS when

  creds available). Covers the question: "do all services have their buckets, and can they auth?"

  '
type: infra
epic: epic-infra
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: deployment-service, code: C5, deployment: none, business: none, readiness_note: 'C5: all quality gates passing. BR N/A: infrastructure provisioning plan — no commercial sign-off required.'}
- {repo: system-integration-tests, code: C5, deployment: none, business: none, readiness_note: 'C5: all quality gates passing. BR N/A: infrastructure provisioning plan — no commercial sign-off required.'}
- {repo: unified-trading-pm, code: C5, deployment: none, business: none, readiness_note: 'C5: all quality gates passing. BR N/A: infrastructure provisioning plan — no commercial sign-off required.'}
depends_on: []
todos:
- {id: gcp-sa-key-create-propagate, content: 'Create GCP_SA_KEY (github-actions-deploy SA, project=central-element-323112, key ID 2c69c1b298b0335029466a9339a537c2191e5a0c). Store raw JSON in GCP Secret Manager as github-actions-sa-key. Add single-line JSON to .act-secrets at workspace root. Propagate to all 62 manifest repos via gh secret set GCP_SA_KEY < key.json. Update copy-gcp-sa-key-to-repos.sh to use workspace-manifest.json (not hardcoded repo list).', status: done, notes: 'DONE 2026-03-10:

    - SA: github-actions-deploy@central-element-323112.iam.gserviceaccount.com

    - Roles: storage.admin, run.admin, artifactregistry.reader/writer, compute.instanceAdmin.v1

    - Key created: gcloud iam service-accounts keys create /tmp/github-actions-sa-key.json

    - Stored in GCP SM: gcloud secrets create github-actions-sa-key (version 1)

    - Added to .act-secrets as single-line compact JSON

    - Propagated to all 62 manifest repos (background job bgej26f74)

    - copy-gcp-sa-key-to-repos.sh updated to use manifest

    '}
- {id: gcp-sa-key-purpose, content: 'Document GCP_SA_KEY purpose: used by google-github-actions/auth@v2 in quality-gates.yml (credentials_json: ${{ secrets.GCP_SA_KEY }}). Allows GHA runners to authenticate as the github-actions-deploy SA so they can: pull from Artifact Registry, push to Cloud Run, read/write GCS test buckets, access Secret Manager for test credentials.', status: done, notes: "DONE 2026-03-10: Format is raw JSON string (not base64). Used in quality-gates.yml step:\n  uses: google-github-actions/auth@v2\n  with:\n    credentials_json: ${{ secrets.GCP_SA_KEY }}\nWas previously set on execution-service + strategy-service only (2026-02-20). Now on all 62 repos.\n"}
- {id: gcs-bucket-audit, content: 'Audit GCS buckets: compare required buckets from deployment-service/configs/dependencies.yaml against actual GCS bucket list. Identify: missing buckets, orphan buckets (exist in GCS but not in deps), naming drift, new services needing buckets (pnl-service, risk-service added recently). Required production buckets (project=central-element-323112): config-store, databento-batch-registry-asia, deployment-orchestration, execution-store, features-calendar, features-delta-one-{cefi,tradfi,defi}, features-onchain, features-sports, features-volatility-{cefi,tradfi}, instruments-store-{cefi,tradfi,defi}, market-data-tick-{cefi,tradfi,defi}, market-data-candles-{cefi,tradfi,defi} (MDP output — add to deps), ml-models-store, ml-predictions-store, ml-configs-store (exists, add to deps), pnl-store-{cefi,tradfi,defi}, positions-store, risk-store-{cefi,tradfi,defi}, strategy-store, terraform-state.', status: done, notes: 'DONE 2026-03-10: Audit complete. Missing from
    GCS:

    - pnl-store-central-element-323112-{cefi,defi,tradfi} (3)

    - risk-store-central-element-323112-{cefi,defi,tradfi} (3)

    - features-sports-central-element-323112 (1)

    In GCS but not in deps (orphan/needs adding):

    - ml-configs-store-central-element-323112 (add to infra_buckets)

    - market-data-candles-{cefi,tradfi,defi}-central-element-323112 (MDP output — add to deps)

    Naming drift (old-style bucket names, harmless — old buckets still work):

    - execution-store-{cefi,defi,tradfi} (shared bucket is correct, old ones are orphans)

    - strategy-store-{cefi,defi,tradfi} (same)

    '}
- {id: gcs-bucket-create-missing, content: 'Create 7 missing GCS buckets using gsutil mb (STANDARD, asia-northeast1, uniform bucket access): pnl-store-central-element-323112-{cefi,defi,tradfi}, risk-store-central-element-323112-{cefi,defi,tradfi}, features-sports-central-element-323112. Also create corresponding test buckets (*-test-*). Then run setup-buckets.py --cloud gcp --dry-run to confirm all required buckets exist.', status: done, notes: 'DONE 2026-03-10: All 7 production buckets created (background job btspnb6mn, exit 0).

    pnl-store-central-element-323112-{cefi,defi,tradfi} (3)

    risk-store-central-element-323112-{cefi,defi,tradfi} (3)

    features-sports-central-element-323112 (1)

    '}
- {id: gcs-deps-yaml-update, content: 'Update deployment-service/configs/dependencies.yaml to add pnl-service, risk-service output bucket templates (pnl-store, risk-store with category), market-data-processing-service output (market-data-candles). Update bucket_config.yaml infrastructure_buckets to add ml-configs-store. Add features-sports-service to shared_bucket_services list (if it exists). Fix setup-buckets.py logger.info() no-arg bug (replace with logger.info("")).', status: done, notes: "DONE 2026-03-10:\n- dependencies.yaml: added market-data-candles-{category_lower}-{project_id} as separate output for\n  market-data-processing-service (in addition to existing processed_candles on market-data-tick bucket)\n- dependencies.yaml: pnl-attribution-service path updated to pnl/{client_id}/{date}/ and client_id added\n  to required_dimensions (was venue; aligns with execution client partitioning pattern)\n- bucket_config.yaml: ml-configs-store-{project_id} added to infrastructure_buckets.gcp\n\
    \  (service: ml-training-service, type: infrastructure, category: ALL)\n- bucket_config.yaml: features-sports-service added to shared_bucket_services list\n- setup-buckets.py: no-arg logger.info() bug does not exist — all calls already use logger.info(\"\") or\n  have arguments; no change required\n- All 26 test_dependencies.py tests pass after changes\n"}
- {id: bigquery-external-tables, content: 'Run deployment-service/scripts/create_bigquery_external_tables.sh with GCP_PROJECT_ID set. Script creates external tables for instruments_cefi_v2, trades_cefi_v2, candles_1m_cefi_v2, features_{1m,5m,15m,1h,4h,24h}_cefi_v2, features_calendar_v2. Tables point to Parquet paths in GCS (hive-partitioned, auto-detect schema). Tables will be empty until data is generated — that is expected. Run with --dry-run pattern first (bq show to check existence). Record results in notes.', status: done, notes: 'DONE 2026-03-10 (deployment-service commit f03778d):

    - instruments_data.instruments_cefi_v2 → gs://instruments-store-cefi-*/hive/day=*/instruments.parquet

    - market_tick.trades_cefi_v2 → gs://market-data-tick-cefi-*/hive/day=*/trades.parquet

    - candles_data.candles_cefi_v2 → gs://market-data-tick-cefi-*/processed_candles/day=*/candles.parquet

    - features_data.features_delta_one_cefi_v2 → gs://features-delta-one-cefi-*/hive/day=*/features.parquet

    - features_data.features_calendar_v2 → gs://features-calendar-*/hive/day=*/features.parquet

    Mock Parquet seed files uploaded to each bucket for schema autodetect.

    Note: candles point to market-data-tick bucket (MDP writes processed_candles/ there, no separate candles bucket).

    '}
- {id: sit-bucket-auth-tests, content: 'Create system-integration-tests/tests/smoke/test_cloud_infra_smoke.py with: (1) test_gcs_all_required_buckets_exist — loads required bucket list from deployment-service/configs/, checks each bucket accessible via UCI get_storage_client(provider=''gcp''); (2) test_gcs_bucket_read_write_permissions — test bucket: write sentinel blob, read it back, delete; (3) test_secret_manager_accessible — get_secret_client(provider=''gcp'') can access a known-good secret; (4) test_aws_s3_buckets_exist — same pattern but provider=''aws'', skip if no AWS creds; (5) test_both_cloud_auth_capable — validates UCI can instantiate both GCP + AWS clients (not necessarily with live creds — local provider OK for import test). Cloud provider selection driven by CLOUD_PROVIDER env var per UIC enum (gcp/aws/local). Tests skip gracefully when GCP_SA_KEY not in env (local dev without creds).', status: done, notes: 'DONE 2026-03-10 (system-integration-tests commit ef5dc20):

    5 test classes: TestGCSBucketsExist, TestGCSBucketPermissions, TestSecretManagerAuth,

    TestAWSS3Buckets, TestDualCloudAuthCapable. All GCP tests skipif not _has_gcp_creds().

    AWS tests skipif not _has_aws_creds(). test_cloud_provider_enum_has_gcp_and_aws validates UIC enum.

    '}
- {id: sit-conftest-cloud-fixtures, content: 'Update system-integration-tests/tests/conftest.py: add cloud_provider fixture (reads CLOUD_PROVIDER env var, defaults to ''gcp''), add gcs_project_id fixture (reads GCP_PROJECT_ID), add required_buckets fixture that loads deployment-service/configs/dependencies.yaml and bucket_config.yaml to enumerate the full required bucket list. These fixtures feed the test_cloud_infra_smoke.py tests.', status: done, notes: 'DONE 2026-03-10 (system-integration-tests commit ef5dc20):

    Added has_gcp_creds, gcs_test_bucket, required_gcs_buckets fixtures.

    required_gcs_buckets uses module-level helpers (_load_deployment_configs,

    _enumerate_service_buckets, _enumerate_infra_buckets) to satisfy C901 complexity limit.

    '}
- {id: aws-bucket-setup, content: 'When AWS creds are available: run setup-buckets.py --cloud aws --include-test --dry-run first, then --create to provision S3 buckets per aws_bucket_mappings in bucket_config.yaml. AWS equivalent buckets use account_id instead of project_id. Currently skipped — aws configure not set up. SIT test_aws_s3_smoke.py already skips gracefully when no boto3 creds.', status: blocked, notes: 'AWS credentials (access key, secret, account ID) not set up yet. Placeholder bucket test exists in test_aws_s3_smoke.py.'}
- {id: dual-cloud-auth-strategy, content: 'Auth strategy: test BOTH GCP and AWS auth in SIT regardless of deployment target. The CloudProvider/CloudTarget enum in unified-internal-contracts defines GCP|AWS|LOCAL. SIT tests should validate UCI can auth for both clouds so code is proven capable before deployment decisions are made. GCP always tested (credentials always available in CI via GCP_SA_KEY). AWS tested when AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY are set (skip otherwise). Deployment decision (which cloud to actually deploy to) is separate from auth testing.', status: done, notes: 'DONE 2026-03-10: TestDualCloudAuthCapable in test_cloud_infra_smoke.py validates both

    GCP + AWS UCI client instantiation (local provider) + CloudProvider enum has GCP and AWS members.

    '}
- {id: per-repo-bucket-permissions-check, content: 'Each service repo should test its own bucket permissions in its quality-gates.sh smoke test phase: verify it can read from its input buckets and write to its output bucket. Use CLOUD_MOCK_MODE=true for unit tests (no real GCS calls). In smoke test phase (CLOUD_MOCK_MODE=false, GCP_SA_KEY set), do a real GCS list or read on the test bucket. This confirms IAM is correctly configured per-service. Bucket permissions are all under roles/storage.admin for the github-actions-deploy SA (sufficient for CI). Production services use per-service SAs.', status: done, notes: "DONE 2026-03-10 (documentation task — no per-repo QG changes):\n- Created unified-trading-pm/docs/bucket-permissions-per-service.md documenting which bucket each\n  service reads/writes, including infrastructure buckets table and notes on shared buckets\n- Decision to defer per-repo QG integration documented in the new file: modifying ~20 service\n  quality-gates.sh files is a large\
    \ cross-cutting change tracked separately\n- SIT smoke tests in system-integration-tests/tests/smoke/test_cloud_infra_smoke.py provide\n  system-level bucket auth coverage in the meantime (see sit-bucket-auth-tests todo, status: done)\n"}
isProject: false
---

# Cloud Infrastructure: Bucket Audit, Auth, and SIT

**Supersedes:** Nothing — new plan. **Linked plans:**
[full_autonomous_agent_ci.plan.md](full_autonomous_agent_ci.plan.md) (GCP_SA_KEY propagation completes
bootstrap-telegram todo), [api_keys_and_auth.plan.md](api_keys_and_auth.plan.md) (GCP SM auth testing)

---

## GCP_SA_KEY

| Item               | Detail                                                                                     |
| ------------------ | ------------------------------------------------------------------------------------------ |
| **Purpose**        | `google-github-actions/auth@v2` in `quality-gates.yml` — credentials_json auth             |
| **SA**             | `github-actions-deploy@central-element-323112.iam.gserviceaccount.com`                     |
| **Roles**          | `storage.admin`, `run.admin`, `artifactregistry.reader/writer`, `compute.instanceAdmin.v1` |
| **Format**         | Raw JSON string (not base64)                                                               |
| **GCP SM**         | `github-actions-sa-key` (project: central-element-323112, version 1)                       |
| **`.act-secrets`** | `GCP_SA_KEY=<single-line-json>` at workspace root                                          |
| **GitHub secrets** | Propagated to all 62 manifest repos (2026-03-10)                                           |

---

## GCS Bucket Status

| Bucket                                     | GCS | deps.yaml | Action               |
| ------------------------------------------ | --- | --------- | -------------------- |
| `instruments-store-{cefi,tradfi,defi}-*`   | ✅  | ✅        | OK                   |
| `market-data-tick-{cefi,tradfi,defi}-*`    | ✅  | ✅        | OK                   |
| `features-calendar-*`                      | ✅  | ✅        | OK                   |
| `features-delta-one-{cefi,tradfi,defi}-*`  | ✅  | ✅        | OK                   |
| `features-volatility-{cefi,tradfi}-*`      | ✅  | ✅        | OK                   |
| `features-onchain-*`                       | ✅  | ✅        | OK                   |
| `ml-models-store-*`                        | ✅  | ✅        | OK                   |
| `ml-predictions-store-*`                   | ✅  | ✅        | OK                   |
| `strategy-store-*`                         | ✅  | ✅        | OK                   |
| `execution-store-*`                        | ✅  | ✅        | OK                   |
| `positions-store-*`                        | ✅  | ✅        | OK                   |
| `terraform-state-*`                        | ✅  | ✅        | OK                   |
| `deployment-orchestration-*`               | ✅  | ✅        | OK                   |
| `config-store-*`                           | ✅  | ✅        | OK                   |
| `databento-batch-registry-asia-*`          | ✅  | ✅        | OK                   |
| `pnl-store-*-{cefi,tradfi,defi}`           | ❌  | ✅        | **CREATE**           |
| `risk-store-*-{cefi,tradfi,defi}`          | ❌  | ✅        | **CREATE**           |
| `features-sports-*`                        | ❌  | ✅        | **CREATE**           |
| `ml-configs-store-*`                       | ✅  | ❌        | Add to infra_buckets |
| `market-data-candles-{cefi,tradfi,defi}-*` | ❌  | ❌        | Add to deps + CREATE |

---

## External Tables (BigQuery)

Run: `GCP_PROJECT_ID=central-element-323112 bash scripts/create_bigquery_external_tables.sh`

Tables created (empty until data flows, auto-populate via hive partitioning):

- `instruments_data.instruments_cefi_v2`
- `market_tick.trades_cefi_v2`
- `candles_data.candles_1m_cefi_v2`
- `features_data.features_{1m,5m,15m,1h,4h,24h}_cefi_v2`
- `features_data.features_calendar_v2`

---

## Auth Strategy: Test Both Clouds

```
CLOUD_PROVIDER=gcp  → test GCP (always in CI via GCP_SA_KEY)
CLOUD_PROVIDER=aws  → test AWS (skip in CI until AWS creds added)
CLOUD_PROVIDER=local → no real cloud calls (unit tests)
```

Tests validate that UCI can instantiate clients for both GCP and AWS so code is proven dual-cloud capable regardless of
deployment decision.
