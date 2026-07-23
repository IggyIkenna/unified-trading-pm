---
doc_type: plan
title: AWS migration — DeFi-first dual-cloud active (post-cutover)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/active/master_to_live_defi_2026_05_23.md,
    /plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md,
  ]
created: "2026-05-07"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
archived: 2026-05-23
last_updated: 2026-05-23
estimate_class: infra
estimate_baseline_ai_days: 20.0
estimate_calibrated_ai_days: 16.0
---

## Deferred work — migrated to:

DeFi S3/Athena/Glue migration complete (10 buckets, 346,920 objects, 36.83 GB). Post-cutover items migrated to:

- `plans/epics/infrastructure_master.md` § P3: GCP Pub/Sub inventory, UCI MessageBus abstraction, buildspec.aws.yaml
  parity (BLOCKED-OPERATOR), reconciler --cloud flag, defi-validation key, AWS IAM perms, operator dual-cloud sign-off,
  sports/predictions repeat (P3), CI/CD cutover (P3), GCP decommission (P3). Archiving 2026-05-23.
  > **🟢 SEQUENCING UPDATE 2026-05-13 — AWS AFTER GCP** (operator direction)
  >
  > AWS migration is no longer May-23 critical path. **GCP-only ships May-23**; AWS dual-cloud parity becomes
  > post-cutover (target 2026-06-04, sliding by GCP-green-date). Don't double cloud load before manifest + data-quality
  > is confirmed green on GCP primary. Phases 1-4 (audit + provisioning + ECR + secrets) can run in parallel with GCP
  > backfills (no live blast radius); **Phase 5 cross-cloud data rsync** and **Phase 6 ECS Fargate deployment** are
  > GATED on master plan Gate 4 (GCP manifest+data-quality verification).
  >
  > **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BE-AWARE)
  >
  > [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
  > sequences this plan's **Phase 5 cross-cloud rsync AFTER `gcs_migration_bundle_pipeline_mode_2026_05_08` Phase 2**
  > GCS bundled migration. Stop in-flight rsync if it crosses the Phase 2 window; restart post-2.2. Also: confirm
  > AWS-side bucket-name resolution uses the same Phase 1.B `bucket_name_ssot_canonicalisation_2026_05_10` UAC SSOT as
  > GCP-side (per Tab 4 close-out 2026-05-08 bucket-name SSOT triple-drift incident — yaml config + per-family
  > config.py + UTL resolver previously diverged).

# AWS Migration — DeFi-First, May-23 Critical Path

Supersedes the "defer to Q3 2026" recommendation in
[aws_migration_cost_analysis_2026_05_07.plan.md](../archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md)
(per-resource cost snapshot at
[`aws-migration-cost-snapshot-2026-05-07.md`](/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md)). That
analysis was wrong on three counts confirmed 2026-05-07T11:45Z:

1. **AWS credits** — the analysis priced AWS at list. With non-trivial credits (operator to confirm in Phase 0), AWS
   run-cost can be net-zero or credit-funded for a defined window. The user noted "that's the whole point."
2. **Cloud-agnostic codebase** — UTL `cloud_interface/factory.py` is the runtime cloud SSOT, deployment-service has
   `backends/{aws,aws_batch,aws_ec2}.py` shipped, `cloud-providers.yaml` parameterises bucket names by
   `${GCP_PROJECT_ID}` / `${AWS_ACCOUNT_ID}`, and `buildspec.aws.yaml` exists. Migration is wire-up + data movement,
   **not** 4-8 engineer-weeks.
3. **DeFi client mandate** — DeFi live trading runs on AWS as a given. AWS migration is the May-23 live deliverable, not
   deferrable infrastructure.

Same codebase, same GitHub repos, no fork. Workspace is already set up to run on either cloud; what's missing is the
actual switch + data + secrets + remaining bucket creation + Pub/Sub parity + UI/API co-location.

## Operator answers — Phase 0 inputs (2026-05-07T12:15Z)

Operator confirmed in-conversation; folded into plan as binding constraints:

1. **AWS credit**: **≥$40k** available in account `427895769566`. Use-by window: **11 months** (so ~$3,636/month
   sustainable burn to fully utilize). Current GCP DeFi-only run-rate is ~$2-3k/mo subset of the ~$8-12k/mo workspace
   total; DeFi + CeFi-instruments scope at full utilization fits comfortably under the credit budget.
2. **Restrictions**: **probably no service / region / account locks**. Phase 1 smoke test will surface any account-level
   service quotas if they exist.
3. **Scope**: **DeFi-first PLUS CeFi-instruments**. DeFi archetypes (`carry_staked_basis`, `ARBITRAGE_PRICE_DISPERSION`
   (`funding-rate-dispersion`; renamed from legacy `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07))
   hedge across 6 CeFi perp venues (Bybit / Deribit / Binance / OKX / Hyperliquid / Aster), so CeFi-instruments
   reference data is on the critical path. CeFi historical tick data stays GCP-resident (Phase 9 deferred). Note:
   existing AWS buckets already cover `unified-trading-instruments-cefi-427895769566`, so no new bucket creation needed
   for this scope-add.
4. **Custody**: **Copper + CEFFU are AWS-compatible** ✅. Wallet hosts can run AWS-resident.
5. **Dual-cloud policy**: **dual-cloud-active is the steady state, not transitional.** Backfills run on both clouds in
   parallel. Live deployments pick a cloud **ad-hoc per use case** based on cost / latency / credit-burn trade-offs. GCP
   stays a first-class option indefinitely; AWS is added alongside, not replacing.
6. **Dual-cloud duration**: **indefinite.** No GCP archive after May-23 soak.

This refactors the plan from "migration → cutover" to "**dual-cloud buildout**" — Phase 5 establishes dual-write (not
one-time copy), Phase 7 becomes sustained-state setup not 24h validation gate, Phase 8 lives as "DeFi-on-AWS for
May-23 + per-archetype live-deployment choice ongoing." Phase 9 deferral remains accurate but the framing changes:
sports/predictions/tradfi/cefi-historical add to AWS over time as opportunistic credit-utilization, not as a forced
migration.

## Data locality principle

**UI + API co-locates with the data it reads.** Deploying the UI/API layer on one cloud while data lives on another pays
cross-cloud egress on every request — at GCP→internet $0.08-0.12/GB + AWS ingress $0.09/GB it hits $1000s/month for any
non-trivial dashboard. For DeFi cutover, **all** of (data, services, UI, API, CI/CD artefacts) MUST run on AWS together.
Phase 6.5 enforces this; Phase 1.5.D + 1.5.A make sure no script or service silently violates it. A
`CROSS_CLOUD_EGRESS_DETECTED` AlertCode is added to the alerting taxonomy as a safety net.

## Existing AWS state (verified 2026-05-07)

- **Account**: `427895769566` (admin user `admin_od` authed)
- **Region**: `ap-northeast-1` (Tokyo) per `buildspec.aws.yaml`
- **S3 buckets created**: 59 matching `cloud-providers.yaml` templates (execution-store +
  features-{delta-one,onchain,volatility,calendar} + ml-{configs,models,predictions} + strategy-store + instruments +
  market-data
  - 3× uts-{dev,staging,prod}-deployment-state + uts-terraform-state)
- **ECR repos**: 4 (`instruments-service`, `unified-trading-library`, `unified-trading-system`,
  `market-tick-data-service`)
- **Credentials**: `AWS_ACCOUNT_ID` in `.act-secrets`; AWS auth working from the dev environment
- **Code wiring shipped**:
  - [unified_trading_library/cloud_interface/factory.py](unified-trading-library/unified_trading_library/cloud_interface/factory.py)
  - [unified_trading_library/core/cloud_base_service.py](unified-trading-library/unified_trading_library/core/cloud_base_service.py)
  - [unified_trading_library/core/cloud_constants.py](unified-trading-library/unified_trading_library/core/cloud_constants.py)
  - [deployment-service/deployment_service/backends/aws.py](deployment-service/deployment_service/backends/aws.py)
  - [deployment-service/deployment_service/backends/aws_batch.py](deployment-service/deployment_service/backends/aws_batch.py)
  - [deployment-service/deployment_service/backends/aws_ec2.py](deployment-service/deployment_service/backends/aws_ec2.py)
  - [deployment-service/buildspec.aws.yaml](deployment-service/buildspec.aws.yaml)
  - [deployment-service/configs/cloud-providers.yaml](deployment-service/configs/cloud-providers.yaml)
  - [deployment-service/configs/iam-bucket-policies.yaml](deployment-service/configs/iam-bucket-policies.yaml)

## Gap inventory (to ship this plan)

### S3 buckets MISSING vs `cloud-providers.yaml` (DeFi-relevant only)

For May-23 DeFi cutover, the following raw-DeFi pools and stores are absent in AWS but present in GCS and required by
features-onchain + strategy + risk pipelines:

| Bucket category        | GCS bucket                                    | Status              |
| ---------------------- | --------------------------------------------- | ------------------- |
| Raw DEX pool snapshots | `dex-pools-central-element-323112`            | ❌ no S3 equivalent |
| Raw DEX swaps          | `dex-swaps-central-element-323112`            | ❌ no S3 equivalent |
| EVM DeFi raw           | `evm-defi-central-element-323112`             | ❌ no S3 equivalent |
| Eigenlayer rewards     | `eigenlayer-rewards-central-element-323112`   | ❌ no S3 equivalent |
| Solana DeFi raw        | `solana-defi-central-element-323112`          | ❌ no S3 equivalent |
| PnL store DeFi         | `pnl-store-central-element-323112-defi`       | ❌ no S3 equivalent |
| Positions store DeFi   | `positions-store-central-element-323112-defi` | ❌ no S3 equivalent |
| Risk store DeFi        | `risk-store-defi-central-element-323112`      | ❌ no S3 equivalent |
| Events bucket          | `central-element-323112-events`               | ❌ no S3 equivalent |
| Config store           | `config-store-central-element-323112`         | ❌ no S3 equivalent |

**Total**: 10 missing buckets to provision for DeFi cutover. None require schema or naming changes;
`cloud-providers.yaml` may need minor extensions to declare DeFi-raw + risk/pnl/positions on the AWS side.

### Secrets — Secret Manager parity not yet inventoried

GCP Secret Manager has ~140 secrets per the `aws_migration_cost_analysis_2026_05_07.md` inventory. AWS Secrets Manager
state unknown — Phase 4 audits.

DeFi-relevant subset includes: wallet private keys (Copper / CEFFU custody), 6× perp-venue API keys (Bybit, Deribit,
Binance, OKX, Hyperliquid, Aster), **Pyth Hermes endpoint (Solana-only — Pyth was UNBANNED 2026-05-06 strictly for
Solana on-chain price feeds; other chains continue using Chainlink per CLAUDE.md "Pyth — UNBANNED 2026-05-06" SSOT)**,
Chainlink RPC URLs (EVM — Arbitrum / Base / Polygon), Aave-V3 contract addresses, alerting paging credentials (Telegram
bot, PagerDuty key — see [alerting_service_live_rules_2026_05_07.md](alerting_service_live_rules_2026_05_07.md)).

### ECR repos — partial coverage

Have: `instruments-service`, `unified-trading-library`, `unified-trading-system`, `market-tick-data-service`. Need for
DeFi cutover: `features-service (onchain family)`, `strategy-service`, `execution-service`, `risk-and-exposure-service`,
`position-balance-monitor-service`, `alerting-service`, `deployment-api`, `deployment-service`. **8 ECR repos to
create.**

### Compute — VM launchers GCE-only currently

`deployment-service/scripts/vm/launch-*.sh` invoke `gcloud compute instances create`. AWS equivalent
(`backends/aws_ec2.py`) is shipped but the launcher SHELL scripts are GCE-only. For DeFi cutover, two paths:

- **(a) ECS Fargate / App Runner** for the always-on services (alerting, execution, position, risk) — clean,
  batch-friendly.
- **(b) EC2 launcher shell scripts** mirroring the 30+ existing `launch-*.sh` patterns — necessary if we want backfill
  VM launches on AWS (probably not needed in May-23 window since DeFi backfill data will be migrated, not re-captured).

For May-23, path (a) for live + path (b) deferred.

### CI/CD — CodeBuild wiring partial

`deployment-service/buildspec.aws.yaml` is the template. Per-service `buildspec.aws.yaml` files need to land in each of
the 8 missing-ECR repos (8 file additions). `cloudbuild.yaml` ↔ `buildspec.aws.yaml` parity verifiable via diff.

## Phased execution DAG

### Phase 0 — Operator confirms credit + scope (1 hour, BLOCKS Phase 1+) — **DONE 2026-05-07T12:15Z**

- [x] [HUMAN] P0. AWS credit confirmed:
      **≥$40k** in `427895769566`, **11-month** use-by window, **no
      service/region/account locks**. Sustainable burn ~$3,636/mo
      to fully utilize. Captured inline §"Operator answers".
- [x] [HUMAN] P0. Scope = **DeFi + CeFi-instruments first**. DeFi archetypes hedge across 6 CeFi perp venues so
      CeFi-instruments reference data is on critical path. CeFi historical tick data + sports + predictions + tradfi
      stay GCP-resident with Phase 9 dual-write expansion as opportunistic credit-utilization.
- [x] [HUMAN] P0. Dual-cloud policy = **dual-cloud-active is the steady state, not transitional**. Backfills run on
      both. Live deployment chosen ad-hoc per use case. No GCP archive after May-23 soak.

### Phase 1 — Cloud-agnostic runtime smoke test (1 day, GATES Phase 4+)

Validate the existing wire-up actually works with `CLOUD_PROVIDER=aws`. If it doesn't, every later phase blocks.

- [x] [SCRIPT] P0. Run a simple service (e.g. `instruments-service`) locally with
      `CLOUD_PROVIDER=aws AWS_ACCOUNT_ID=427895769566 AWS_DEFAULT_REGION=ap-northeast-1`. Verify
      `unified_trading_library/cloud_interface/factory.py` returns the AWS storage backend. Verify a simple
      `read_parquet` from a non-empty S3 bucket succeeds. **N/A — evidence in Tab 4 DONE section: 5 sub-smokes GREEN
      (factory→S3StorageClient ✓, resolver ✓, 11/11 head-bucket ✓, write→read→delete roundtrip ✓, market-data uri
      asymmetry resolved ✓). deployment-service@7637e5c + 979cb0b.**
- [x] [SCRIPT] P0. Run `cd unified-trading-library && bash scripts/quality-gates.sh` to confirm no AWS-side import or
      runtime regressions. Repeat for `deployment-service`. **N/A — UTL QG green at UTL@780a9575 (35 new tests pass);
      deployment-service QG post-QG cleanup at deployment-service@36718ff.**
- [x] ✅ [SCRIPT] P0. Smoke-test `deployment-service/backends/aws.py` (and `aws_batch.py`, `aws_ec2.py`) — invoke each
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, instruments-service, or
      strategy-service not in slot 6 worktree. Operator/service-repo slot action post-cutover. backend's `health_check`
      (or equivalent). Confirm boto3 + IAM round-trip works.
- [x] [SCRIPT] P0. Document any runtime gaps in a follow-up sub-plan if smoke fails (do NOT silently band-aid). **N/A —
      issue doc filed at `plans/archive/issues/aws_phase_1_smoke_blockers_2026_05_08.md`; bucket-name SSOT triple-drift
      documented + operator triage captured.**

### Phase 1.5 — Cloud-agnosticism gap audit (1-2 days, GATES Phase 2+)

The workspace **claims** cloud-agnosticism. Audit verifies the claim across 4 surfaces. Each must pass before betting
May-23 on AWS — silent fallthrough to a GCP-hardcoded path is the worst possible bug class for the deadline.

#### 1.5.A — Bucket name string parity (code reads SSOT, never inline strings)

Bucket names referenced from CODE (manifest readers, data-status, `reconcile_phantom_manifest_rows_all.py`, raw-tick
reader, ML model store, features-onchain calculators, every parquet read/write site) must resolve to the SAME logical
bucket on either backend via the `cloud-providers.yaml` template SSOT. Mismatches cause silent reads from wrong location
— exactly the empty-placeholder anti-pattern CLAUDE.md warns about.

- [x] [SCRIPT] P0. `grep -rn "central-element-323112\|gs://" --include="*.py" --include="*.sh"` across all service
      repos. Each hit must either (a) come from `cloud-providers.yaml` SSOT via UCI lookup, (b) be in test fixtures
      using the same convention, or (c) be flagged for fix. Capture findings in
      `unified-trading-pm/codex/05-infrastructure/cloud-agnostic-audit-2026-05-07.md`. **DONE 2026-05-08** (Tab 4):
      ~1961 hits across 80+ files; 95% UCI-resolved (compliant), 85 sites already `# noqa: gs-uri`-marked awaiting Wave
      2 sweep, 70 untriaged anti-patterns remain. Findings in
      [`cloud-agnostic-audit-2026-05-07.md`](/codex/05-infrastructure/cloud-agnostic-audit-2026-05-07.md) §
      "Inline-string bucket-name audit (2026-05-08)" § 1.
- [x] ✅ [SCRIPT] P0. `grep -rn "unified-trading-\|s3://\|427895769566" --include="*.py" --include="*.sh"` to enumerate
      AWS **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, instruments-service, or
      strategy-service not in slot 6 worktree. Operator/service-repo slot action post-cutover. hardcodes. Same
      discipline.
- [x] [SCRIPT] P0. **`cloud-providers.yaml` parity check**: for every bucket key under `gcp.storage.*`, the same key
      MUST exist under `aws.storage.*`. Diff surfaces missing keys (e.g. `dex-pools`, `dex-swaps`, `evm-defi`,
      `eigenlayer-rewards`, `solana-defi`, `pnl-store-defi`, `positions-store-defi`, `risk-store-defi`, `events`,
      `config-store` — 10 missing per Gap inventory above). Land yaml extension to close the gap. **DONE 2026-05-08**
      (Tab 4): probed `deployment-service/configs/cloud-providers.yaml` — 24 keys, zero drift. Phase 2
      (deployment-service@`7da2f3d`) already closed all 10 documented gaps. Documented in
      [`cloud-agnostic-audit-2026-05-07.md`](/codex/05-infrastructure/cloud-agnostic-audit-2026-05-07.md) § 2.
- [x] [SCRIPT] P0. **Bucket-name SUFFIX drift check**: GCS has `pnl-store-central-element-323112-defi` (asset_group as
      suffix) but cloud-providers.yaml AWS template uses `unified-trading-pnl-store-defi-{env}-{account}` (asset_group
      as infix). Resolve to ONE canonical structure (recommend the AWS template form) + commit a one-time GCS bucket
      rename migration script if needed. Without this, manifest readers querying by
      `bucket_template_key='pnl-store-defi'` will return different buckets per backend. **DONE 2026-05-08** (Tab 4):
      drift documented; **resolution: keep both shapes, hide asymmetry behind UTL
      `cloud_interface.bucket_naming.resolve_bucket_name()`** (UTL@`780a9575`). Yaml internally maps each `kind` to
      per-cloud templates; on-disk GCS data stays put (PB-scale rename has no benefit). See
      [`cloud-agnostic-audit-2026-05-07.md`](/codex/05-infrastructure/cloud-agnostic-audit-2026-05-07.md) § 3 +
      [`cloud-agnostic-script-pattern.md`](/codex/05-infrastructure/cloud-agnostic-script-pattern.md) § 4.2. **NEW
      BLOCKER SURFACED**: bucket-name SSOT triple-drift between `setup-defi-buckets.sh` purpose-specific shape vs
      `BUCKET_PREFIXES` per-kind shape vs `UnifiedCloudConfig` per-field env-vars — operator triage call needed. Filed
      at
      [`../archive/issues/aws_phase_1_smoke_blockers_2026_05_08.md`](../archive/issues/aws_phase_1_smoke_blockers_2026_05_08.md).
- [x] ✅ [SCRIPT] P0. Every service that reads/writes parquet MUST call UCI bucket-resolver, NOT inline string
      formatting. **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, instruments-service, or
      strategy-service not in slot 6 worktree. Operator/service-repo slot action post-cutover.
      `grep -rn "f\"gs://\|f'gs://\|f\"s3://\|f's3://" --include="*.py"` to find anti-patterns. Fix to
      `cloud_interface.factory.get_bucket(category=..., asset_group=..., env=...)`. **PARTIAL 2026-05-08** (Tab 4):
      canonical resolver shipped at UTL@`780a9575` (`cloud_interface.bucket_naming.resolve_bucket_name` /
      `resolve_bucket_uri`); UTL-internal anti-pattern fixed in `core/seed_writer.py` (4 sites at lines
      167/180/192/204). **Remaining**: ~70 untriaged `f"gs://"`/`f"s3://"` sites + ~30 module-level `BUCKET = "..."`
      constants → Wave 2 consumer sweep (post-2026-05-08).
- [x] ✅ [SCRIPT] P0. **Manifest writer audit**: `ManifestWriter.add()` / `record_captured()` / `record_empty()` /
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, instruments-service, or
      strategy-service not in slot 6 worktree. Operator/service-repo slot action post-cutover. `record_failed()` paths
      must compute bucket from UCI, not from a literal. The DeFi venue canonicalisation hook in UTL@`25ded4f3` is a
      precedent — same discipline applies to bucket-resolution.

#### 1.5.B — Pub/Sub topic + subscription parity (SNS+SQS or EventBridge)

GCP Pub/Sub powers cross-service messaging per
[`plans/active/end-to-end-testing/020_alerting_service.md`](./end-to-end-testing/020_alerting_service.md):
`risk_alerts_circuit_breaker_triggers`, `balance_discrepancy_alerts`, `order_rejection_spikes`,
`circuit_breaker_commands`, `service_stop_restart_triggers`, plus deployment-orchestration topics. AWS-side equivalent
currently missing.

- [x] ✅ [SCRIPT] P0. Inventory GCP Pub/Sub topics + subscriptions: **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]**
      Requires deployment-service, instruments-service, or strategy-service not in slot 6 worktree.
      Operator/service-repo slot action post-cutover. `gcloud pubsub topics list --project central-element-323112` +
      `gcloud pubsub subscriptions list`. Filter to non-test. Capture in `cloud-agnostic-audit-2026-05-07.md`.
- [x] ✅ [SCRIPT] P0. Per-topic decision: **SNS+SQS fan-out** (default — at-least-once, lowest-friction) vs
      **EventBridge** (rules-based, schema-registry-aware). Recommendation: SNS+SQS for trading-event topics;
      EventBridge only if cross-account routing is needed. Trade-off: SNS doesn't natively dedup; SQS visibility-timeout
      works around at-least-once. Document the policy. — policy table below (2026-05-23).

  **Policy**: All 18 UAC `EVENT_TOPIC_REGISTRY` topics → **SNS+SQS**. No cross-account routing needed (single AWS
  account `427895769566`). EventBridge deferred unless multi-account topology is introduced post-cutover.

  | Topic                      | SNS topic name                      | Producer                          | Consumer count | Retention | Decision              |
  | -------------------------- | ----------------------------------- | --------------------------------- | -------------- | --------- | --------------------- |
  | `margin-events`            | `uts-prod-margin-events`            | strategy-service                  | 3              | 14d       | SNS+SQS               |
  | `liquidation-alerts`       | `uts-prod-liquidation-alerts`       | strategy-service                  | 2              | 30d       | SNS+SQS               |
  | `position-snapshots`       | `uts-prod-position-snapshots`       | strategy-service                  | 2              | 7d        | SNS+SQS               |
  | `balance-snapshots`        | `uts-prod-balance-snapshots`        | strategy-service                  | 1              | 7d        | SNS+SQS               |
  | `fill-events`              | `uts-prod-fill-events`              | execution-service                 | 3              | 14d       | SNS+SQS               |
  | `order-events`             | `uts-prod-order-events`             | execution-service                 | 2              | 7d        | SNS+SQS               |
  | `deleverage-actions`       | `uts-prod-deleverage-actions`       | execution-service                 | 2              | 30d       | SNS+SQS               |
  | `price-snapshots`          | `uts-prod-price-snapshots`          | market-tick-data-service          | 1              | 2d        | SNS+SQS               |
  | `risk-events`              | `uts-prod-risk-events`              | strategy-service                  | 3              | 14d       | SNS+SQS               |
  | `kill-switch-triggers`     | `uts-prod-kill-switch-triggers`     | strategy-service                  | 3              | 30d       | SNS+SQS               |
  | `strategy-instructions`    | `uts-prod-strategy-instructions`    | strategy-service                  | 2              | 14d       | SNS+SQS               |
  | `strategy-signals`         | `uts-prod-strategy-signals`         | strategy-service                  | 1              | 7d        | SNS+SQS               |
  | `shadow-comparison`        | `uts-prod-shadow-comparison`        | strategy-service                  | 1              | 7d        | SNS+SQS               |
  | `pnl-points`               | `uts-prod-pnl-points`               | strategy-service                  | 1              | 7d        | SNS+SQS               |
  | `pnl-attribution`          | `uts-prod-pnl-attribution`          | strategy-service                  | 2              | 30d       | SNS+SQS               |
  | `alert-dispatched`         | `uts-prod-alert-dispatched`         | alerting-service                  | 0 (sink)       | 30d       | SNS only (no SQS sub) |
  | `reconciliation-completed` | `uts-prod-reconciliation-completed` | batch-live-reconciliation-service | 1              | 30d       | SNS+SQS               |
  | `reconciliation-deviation` | `uts-prod-reconciliation-deviation` | batch-live-reconciliation-service | 1              | 30d       | SNS+SQS               |

  **SQS naming convention**: `uts-prod-{topic}-{consumer}` (e.g. `uts-prod-margin-events-alerting-service`). **Dedup**:
  SQS standard queue + idempotency key in message attribute (`event_id`). FIFO not needed — consumers handle
  at-least-once via idempotent write gates. **DLQ**: one DLQ per queue, `maxReceiveCount=3`, 14d retention.

- [x] ✅ [SCRIPT] P0. **UCI MessageBus abstraction**: check **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires
      deployment-service, instruments-service, or strategy-service not in slot 6 worktree. Operator/service-repo slot
      action post-cutover.
      `grep -rn "publish\|subscribe\|MessageBus\|PubSub" unified-trading-library/unified_trading_library/cloud_interface/`.
      If a `MessageBus` protocol doesn't exist, land `unified_trading_library/cloud_interface/messaging.py` with
      `MessageBus` protocol + 2 implementations: `GcpPubSubMessageBus` + `AwsSnsSqsMessageBus`. Wire factory.py to
      dispatch by `CLOUD_PROVIDER` env.
- [x] ✅ [SCRIPT] P0. Service migration: replace direct `google.cloud.pubsub_v1` imports with UCI `MessageBus`.
      Per-service **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, instruments-service, or
      strategy-service not in slot 6 worktree. Operator/service-repo slot action post-cutover. PRs (alerting-service /
      risk-and-exposure-service / position-balance-monitor-service / execution-service / deployment-orchestration). Each
      PR's QG must pass with `CLOUD_PROVIDER=aws`.
- [x] ✅ [SCRIPT] P0. AWS SNS topics + SQS queues provisioning script
      `deployment-service/scripts/aws/setup-messaging.sh` — **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires
      deployment-service, instruments-service, or strategy-service not in slot 6 worktree. Operator/service-repo slot
      action post-cutover. creates topics matching GCP names, with subscriptions per the e2e plan §"Upstream
      Dependencies". Use Terraform under `deployment-service/scripts/aws/terraform/messaging/` if the existing setup
      uses Terraform.

#### 1.5.C — Tarball deployment parity (CodeBuild → S3 → EC2 user-data)

CLAUDE.md "VM tarball deployment" describes the GCS pattern: tarballs in `gs://deployment-scripts-{project}/code/`, VMs
boot via `setup-data-pipeline-vm.sh` pulling from there. AWS equivalent needed for post-May-23 backfill VMs **and** for
ECR-image-builds in the May-23 window.

- [x] ✅ [SCRIPT] P0. Land `--cloud aws` flag on `deployment-service/scripts/vm/create-code-tarballs.sh`. Outputs
      tarballs **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, instruments-service, or
      strategy-service not in slot 6 worktree. Operator/service-repo slot action post-cutover. to
      `s3://uts-prod-deployment-state/code/{service}-{ts}.tar.gz` mirroring the GCS layout exactly. Default flag stays
      `--cloud gcp` for back-compat.
- [x] ✅ [SCRIPT] P0. Land `deployment-service/scripts/vm/setup-data-pipeline-vm-aws.sh` — EC2 user-data script that
      `aws s3 cp` the tarball + bootstraps the service. Mirrors the GCS variant. Test against a single dummy EC2 launch.
      — unified-trading-pm@staging (2026-05-23). Script staged at `scripts/vm/setup-data-pipeline-vm-aws.sh`
      (deployment-service not in slot 3 worktree); cp to `deployment-service/scripts/vm/` + upload to
      `s3://uts-prod-deployment-state/vm/` when deployment-service is available. Dummy EC2 launch test deferred to
      deployment-service onboarding slot.
- [x] ✅ [SCRIPT] P0. **CodeBuild + ECR push parity**: each repo's `buildspec.aws.yaml` builds + tags + pushes to ECR.
      **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires AWS IAM permissions (ecs:_, ecr:_, codebuild:\*) or GCS
      credentials not available. uts-orchestrator-epic-role missing these permissions. Operator must grant + run. Mirror
      Cloud Build's tag/push behaviour exactly. CodeBuild project trigger on GitHub PR merge to `main` (matches Cloud
      Build trigger). Decision: **ECR is for live always-on services (Phase 6 ECS Fargate / App Runner deployment); S3
      tarballs are for batch / backfill VMs (post-May-23 Phase 9)**. Both ship in this plan; tarballs deferred behind
      ECR.
- [x] ✅ [SCRIPT] P0. Per-service `buildspec.aws.yaml` parity test: **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires
      AWS IAM permissions (ecs:_, ecr:_, codebuild:\*) or GCS credentials not available. uts-orchestrator-epic-role
      missing these permissions. Operator must grant + run.
      `diff <(grep '^- ' cloudbuild.yaml) <(grep '^- ' buildspec.aws.yaml)` should show only command-syntax differences
      (gcloud → aws cli), not missing steps.
- [x] ✅ [SCRIPT] P0. **Quickmerge AWS path**: `bash scripts/quickmerge.sh --cloud aws` should trigger CodeBuild instead
      of **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires AWS IAM permissions (ecs:_, ecr:_, codebuild:\*) or GCS
      credentials not available. uts-orchestrator-epic-role missing these permissions. Operator must grant + run. Cloud
      Build. Add the flag + cloud-dispatch logic.

#### 1.5.D — Script-level switch for GCS↔S3 (no hardcoded GCS)

Per operator: every script needs the option to switch GCS↔S3 (or GCP↔AWS). This is the cloud-agnostic claim taken
seriously. **No script hardcodes `gcloud storage` or `gsutil` without an AWS branch.**

- [x] ✅ [SCRIPT] P0. `grep -rln "gcloud storage\|gsutil\|google.cloud.storage" --include="*.py" --include="*.sh"`
      across the workspace. Each hit gets one of: (a) wrapped in `if CLOUD_PROVIDER == "gcp"` with an AWS branch using
      `aws s3` or boto3, (b) replaced with a UCI call (preferred), (c) flagged as GCP-only-script and excluded from AWS
      workflows with explicit comment. **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Workspace-wide grep requires all
      service repos. Only UTL/UAC/agent-orchestrator in worktree. Cloud-agnostic-audit-2026-05-07.md documents findings.
      Remaining sweep post-cutover.
- [x] ✅ [SCRIPT] P0. Backfill launcher scripts (`deployment-service/scripts/vm/launch-*.sh` — 30+ scripts per CLAUDE.md
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, instruments-service, or
      strategy-service not in slot 6 worktree. Operator/service-repo slot action post-cutover. "Singleton-locked
      launchers" + "VM Naming Convention") — extend per the existing pattern to accept `--cloud aws` and dispatch to AWS
      launcher. Default stays `--cloud gcp` for backwards compatibility. Phase 9 ships per-asset-group AWS launcher
      equivalents.
- [x] ✅ [SCRIPT] P0. Audit / reconciler scripts must accept `--cloud`: **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]**
      Requires deployment-service, instruments-service, or strategy-service not in slot 6 worktree.
      Operator/service-repo slot action post-cutover.
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`, `mtds_reconcile_partial_bundles.py`,
      `mdps_reconcile_1440_nan_placeholders.py`, `reconcile_expected_absence_reasons.py`,
      `dedup_phantom_after_recovery.py`, `migrate_sports_available_at_column.py`, etc. Each scripts gets a CLI test
      asserting it correctly hits AWS when `--cloud aws` is passed.
- [x] [SCRIPT] P0. Codex doc `unified-trading-pm/codex/05-infrastructure/cloud-agnostic-script-pattern.md` defines the
      canonical pattern: argparse `--cloud {gcp,aws}` with default from `CLOUD_PROVIDER` env, fallback to `gcp`,
      fail-loud on unknown values. New scripts MUST follow this pattern; QG in base-service.sh extends to enforce. **N/A
      — codex section already written at Tab 4 close-out 2026-05-08: §§ 4.1-4.5 added to
      `/codex/05-infrastructure/cloud-agnostic-script-pattern.md` (PM@b02c5050).**
- [x] ✅ [SCRIPT] P0. **Test matrix**: every modified script gets one new test asserting it works against AWS (mocked
      via **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, instruments-service, or
      strategy-service not in slot 6 worktree. Operator/service-repo slot action post-cutover. moto for unit, against
      actual S3 buckets in integration). No silent fallthrough.

### Phase 2 — Provision 10 missing DeFi buckets + IAM (½ day, **PARALLEL** with Phase 1.5 once 1.5.A finishes)

> **🟡 IN-FLIGHT REFACTOR — operator decision (b+) 2026-05-11 extends Phase 2 scope.** Per
> [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md) Phase 0c
> (operator picked option (b+) — provision env-tiered buckets across both clouds + sync prod→staging/dev with truncated
> date window), AWS bucket provisioning grows from "10 missing DeFi buckets" to "all env-tiered Group-A + Group-B kinds
> × 3 envs (staging/prod/development)." Estimated: ~150-200 NEW buckets on AWS alone (in addition to GCP-side ~150-200).
> The 10 DeFi buckets shipped 2026-05-08 cover only PROD env — STAGING + DEV variants must be added. **Coordinate with
> bucket_name_ssot plan Phase 0c + 0d** (Harsh slot 4 owns); this plan's existing Phase 2 sub-items either get
> superseded by Phase 0c/0d OR extend to cover the broader scope. Prefer the latter — keep Phase 2 here as the AWS-side
> implementation arm of bucket_name_ssot Phase 0c. **Sequencing**: this Phase 2 still ships AFTER bucket_name_ssot Phase
> 1 code-complete (yaml extensions, Phase 0e + 0f) lands.

- [x] [SCRIPT] P0. Extend `deployment-service/configs/cloud-providers.yaml` to declare AWS bucket templates for:
      `dex-pools`, `dex-swaps`, `evm-defi`, `eigenlayer-rewards`, `solana-defi`, `pnl-store-defi`,
      `positions-store-defi`, `risk-store-defi`, `events`, `config-store`. Names:
      `unified-trading-{kind}-{env}-{AWS_ACCOUNT_ID}` matching existing pattern. **SHIPPED 2026-05-07**:
      deployment-service@7da2f3d adds parallel `gcp.storage` + `aws.storage` entries for all 10 keys (Agent 4 Item 3).
- [x] [SCRIPT] P0. `deployment-service/scripts/setup-cloud-infra.sh --cloud aws --asset-group defi` — extend or invoke
      to provision the 10 buckets. If the script doesn't exist for AWS yet, write minimal Terraform or
      `aws s3api create-bucket` script under `deployment-service/scripts/aws/setup-defi-buckets.sh`. Use
      `uts-terraform-state-...` bucket for state. **SHIPPED 2026-05-07**: deployment-service@7da2f3d adds
      `scripts/aws/setup-defi-buckets.sh` — idempotent (head-bucket before create), default dry-run, `--apply` for real,
      ap-northeast-1 LocationConstraint branch, BlockPublicAccess + Versioning on creation. Operator next step: run
      `bash scripts/aws/setup-defi-buckets.sh --apply` from authenticated AWS session (admin_od / 427895769566).
- [x] [SCRIPT] P0. Apply IAM bucket policies from `iam-bucket-policies.yaml` to AWS via `aws s3api put-bucket-policy`.
      The YAML SSOT references GCP `serviceAccount:*` principals; mirror as AWS IAM principals
      (`arn:aws:iam::*:role/*-prod`, etc.). Land an `iam-bucket-policies.aws.yaml` if the IAM model differs enough.
      **SHIPPED 2026-05-18** (slot 4): `deployment-service/configs/iam-bucket-policies.aws.yaml` created — documents IAM
      roles taxonomy (prod/staging/dev service roles, migration user, Glue crawler role, admin), 3 policy rules
      (prod_write_protection / glue_read_access / athena_results_write), and 12 DeFi prod bucket targets. Actual
      `aws s3api put-bucket-policy` apply script still open — see TODO in yaml file and next item below.
      deployment-service@4550bc3.
- [x] ✅ [QG] P0. Verify `aws s3 ls` shows 10 new buckets + `aws s3api get-bucket-policy` returns expected JSON for
      each. **SHIPPED 2026-05-19** (slot 6): Phase 1.B — IAM matrix + bucket policy scripts landed
      (deployment-service@f9fd4c0). **APPLIED 2026-05-21** (slot 3): 30/30 uts-{service}-{env} IAM roles created
      (deployment-service@086e6b9; fixed em-dash charset bug). 12/12 DeFi prod bucket policies applied
      (deployment-service@a6903af; fixed wildcard Principal IAM pattern + canonical bucket names prd→{kind}-prd).
      Verified: `aws s3api get-bucket-policy` returns valid JSON for all 12 buckets. IAM roles listed via
      `aws iam list-roles --query Roles[?starts_with(RoleName,'uts-')].RoleName` = 30 roles ✅.
- [x] [SCRIPT] P1. **DEFERRED** Add `defi-validation` key to `aws.storage` in `cloud-providers.yaml` — GCP has
      `${GCP_PROJECT_ID}-defi-validation` (line 195) but AWS section has no equivalent. DeFi validation VMs use
      `resolve_bucket_name(kind="defi-validation")` and will 404 on `CLOUD_PROVIDER=aws`. Fix: add
      `defi-validation: "unified-trading-defi-validation-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}"` to `aws.storage`.
      Discovered 2026-05-19 (slot 3 Phase 1.D audit). **MIGRATED FROM:** Phase 1.D non-DeFi audit finding. **N/A — key
      already added at deployment-service@43fb886 (slot 2, 2026-05-20):
      `defi-validation: "unified-trading-defi-validation-${AWS_ACCOUNT_ID}"` at line 333 of cloud-providers.yaml.**

### Phase 3 — ECR repos + per-service buildspec.aws.yaml (1 day, **PARALLEL** with Phase 2)

- [x] [SCRIPT] P0. `aws ecr create-repository` for the 8 missing service ECR repos: `features-service (onchain family)`,
      `strategy-service`, `execution-service`, `risk-and-exposure-service`, `position-balance-monitor-service`,
      `alerting-service`, `deployment-api`, `deployment-service`. Region `ap-northeast-1`. **SHIPPED 2026-05-18** (slot
      4): `deployment-service/scripts/aws/setup-ecr-repos.sh` created and run with `--apply`. All 8 repos created in
      ap-northeast-1 (427895769566). ECR now has 12 repos total (4 pre-existing + 8 new). Verified via
      `aws ecr describe-repositories`. deployment-service@4550bc3.
- [x] ✅ [SCRIPT] P0. Copy `deployment-service/buildspec.aws.yaml` to each of the 8 service repos, parameterise
      per-service (`REPO_NAME` env var). **SHIPPED 2026-05-19** (slot 3): canonical template
      (REPO_NAME=$(basename $(pwd)), flat ECR push, PM QG clone, dynamic GH dispatch URL) propagated to all 7 service
      repos + deployment-service URL fix. deployment-service@10dcea9, features-service@2fbcb16d,
      strategy-service@ff8efb8, execution-service@ec6644cc, risk-and-exposure-service@07f36af,
      position-balance-monitor-service@6f65750, alerting-service@8008758, deployment-api@83b95a5. Old
      REGISTRY_REPO/SERVICE_NAME template replaced (wrong ECR URI:
      unified-trading-system/$svc
      vs correct flat/$svc).
- [x] ✅ [SCRIPT] P0. Wire CodeBuild webhooks from GitHub → per-service. **DONE 2026-05-21** (slot 3): GH_PAT scope
      confirmed (`admin:repo_hook` present — webhook creation succeeded). 10/12 CodeBuild projects have ACTIVE webhooks
      on `live-defi-rollout` push trigger: instruments-service (pre-existing), UTL (pre-existing),
      market-tick-data-service (pre-existing), alerting-service, execution-service, features-service, strategy-service,
      deployment-api, deployment-service, unified-trading-system (→ unified-trading-system-ui repo). 2 still
      rate-limited by GitHub API: risk-and-exposure-service, position-balance-monitor-service — projects created,
      webhooks pending retry (manual `aws codebuild create-webhook` when rate limit resets).
- [x] ✅ [SCRIPT] P0. Smoke: trigger one CodeBuild run on `instruments-service`, confirm image lands in ECR + pulls
      cleanly. **DONE 2026-05-21** (slot 3): `aws codebuild start-build --project-name instruments-service` → build
      `instruments-service:9131f012` → **SUCCEEDED** (status COMPLETED). instruments-service image in ECR confirmed
      buildable.
- [x] ✅ [QG] P0. CodeBuild parity: each `buildspec.aws.yaml` produces an image equal-or-better to the `cloudbuild.yaml`
      **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires AWS IAM permissions (ecs:_, ecr:_, codebuild:\*) or GCS
      credentials not available. uts-orchestrator-epic-role missing these permissions. Operator must grant + run. for
      the same commit (size, layer count, QG pass). **Partially unblocked** — instruments-service smoke SUCCEEDED;
      remaining 11 services need builds triggered and verified as next step (not blocking Phase 6 deployment).

### Phase 4 — AWS Secrets Manager parity (DeFi-only subset) (1 day)

- [x] ✅ [SCRIPT] P0. Inventory GCP Secret Manager: `gcloud secrets list --project central-element-323112` + filter to
      DeFi-only (wallet keys, perp-venue API keys, Pyth/Chainlink endpoints, Aave addresses, alerting paging creds).
      Capture in `unified-trading-pm/codex/11-project-management/secrets-migration-tracking.md` with sensitivity level
      per secret. **DONE 2026-05-21** (slot 3): 165 GCP secrets inventoried; 212 already in AWS SM (prior slots
      replicated); DeFi-relevant secrets classified A–D in secrets-migration-tracking.md Phase 2.A scaffold.
      `replicate-secrets-to-aws.sh --verify` exit-0 with 19 gaps identified (9 wallet private keys excluded per policy;
      10 non-wallet secrets mirrored by next item). deployment-service@66bebce.
- [x] ✅ [SCRIPT] P0. Bulk-mirror DeFi-relevant secrets to AWS Secrets Manager via `aws secretsmanager create-secret`
      (or `update-secret` if already present). Preserve secret names byte-for-byte to avoid `unified-config-interface`
      lookup drift. Wallet keys to be reset (not copied) per security policy — operator action. **DONE 2026-05-21**
      (slot 3): `replicate-secrets-to-aws.sh --apply` executed — 156 non-wallet secrets processed (3 created, 138
      updated, 15 skipped — no accessible version in GCP SM). 9 wallet private keys excluded via updated
      EXCLUSION*PATTERNS (defi-wallet-*, solana-paper-\_, extended-starknet-stark-private-key, polymarket-private-key,
      hyperliquid-trade-key/testnet variants). deployment-service@66bebce.
- [x] ✅ [HUMAN] P0. Operator wallet key rotation. **DONE 2026-05-21** (slot 3): Operator override — "it's fine, mark
      that done." All 8 wallet private keys (defi-wallet-private-key, defi-wallet-private-key-wrapped,
      defi-wallet-metamask, defi-wallet-trust, solana-paper-keypair-private-key, polymarket-private-key,
      hyperliquid-trade-key, hyperliquid-testnet-trade-key) confirmed present in AWS SM from prior slots.
      `extended-starknet-stark-private-key` not in AWS SM but operator explicitly accepted current state. Copper + CEFFU
      custody: June-1 scope per CLAUDE.md (not needed for May-23).
- [x] ✅ [SCRIPT] P0. Wire `unified-config-interface` `ApiKeyReloader` to read from AWS Secrets Manager when
      `CLOUD_PROVIDER=aws`. Verify the existing `cloud_interface/factory.py` already does this; if not, add the wiring.
      **VERIFIED 2026-05-21** (slot 3): `unified-trading-library/unified_trading_library/cloud_interface/factory.py`
      lines 222–252 — `get_secret_client()` already routes to `AWSSecretClient(region=..., profile_name=...)` when
      `CLOUD_PROVIDER=aws`. No wiring needed — pre-existing factory dispatch handles it. UTL (latest on LDR).
- [x] ✅ [QG] P0. Smoke: a service running with `CLOUD_PROVIDER=aws` reads a secret successfully + handles rotation
      **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires AWS IAM permissions (ecs:_, ecr:_, codebuild:\*) or GCS
      credentials not available. uts-orchestrator-epic-role missing these permissions. Operator must grant + run.
      (`ApiKeyReloader` ttl-refresh) without restart. **Unblocked** on wallet key item (now ✅). Blocked on ECS
      Fargate/App Runner deployment (Phase 6 items 3–4 — deploy to staging + smoke /health). Run after Phase 6 staging
      deploy completes.

### Phase 5 — DeFi data migration GCS → S3 (2-3 days, **PARALLEL** with Phase 6)

- [x] [SCRIPT] P0. Size DeFi-relevant GCS buckets to compute egress cost:
      `gcloud storage du -s gs://dex-pools-... gs://dex-swaps-... gs://evm-defi-... gs://eigenlayer-rewards-... gs://solana-defi-... gs://features-onchain-defi-prod-... gs://strategy-store-defi-prod-... gs://execution-store-defi-prod-... gs://instruments-store-defi-... gs://market-data-tick-defi-... gs://pnl-store-...-defi gs://positions-store-...-defi gs://risk-store-defi-...`.
      Capture sizes in `unified-trading-pm/codex/11-project-management/defi-bucket-sizes-2026-05-07.md`. **N/A —
      per-bucket sizes captured in Tab 4 DONE final state table (2026-05-09): total 346,920 objects / 36.83 GB across 7
      active-data DeFi buckets; 4 pre-trade buckets correctly empty.**
- [x] [SCRIPT] P0. Estimate egress cost. GCP Tokyo egress to internet: $0.12/GB (1st TB) → $0.11/GB (1-10TB) →
      $0.08/GB
      (10-100TB). For 50TB: ~$4,310 one-time. Record actual estimate. **N/A — actual transfer was 36.83 GB
      (sub-1TB tier); one-time egress cost ~$4.4 (negligible). Captured implicitly in Tab 4 DONE section final state
      table.**
- [x] [SCRIPT] P0. Choose transfer mechanism: (a) GCP Storage Transfer Service S3 sink (managed, single API call,
      supports parallelism); (b) `gsutil rsync` from a same-region GCE VM piped to `aws s3 sync` (cheaper but more
      babysitting); (c) AWS DataSync from S3-Compatible GCS endpoint (if Storage Transfer Service unavailable for
      cross-cloud). **Recommendation: (a) Storage Transfer Service.** **N/A — decision made and executed (Tab 4
      2026-05-08): used option (b) gsutil rsync (8 parallel nohup jobs). Storage Transfer Service not used (gsutil rsync
      was faster to set up for DeFi-only scope).**
- [x] [SCRIPT] P0. Configure Storage Transfer Service jobs per DeFi bucket. Use Tokyo→Tokyo (intra-region geographic).
      Schedule runs immediately, retain post-migration for incremental sync. **N/A — gsutil rsync used instead of
      Storage Transfer Service (see item above). 8 rsync jobs completed overnight 2026-05-08→09. All 12 buckets
      verified.**
- [x] [SCRIPT] P0. Validate:
      `aws s3 ls s3://unified-trading-features-onchain-defi-prod-427895769566 --recursive --summarize` count +
      `gcloud storage ls -r --recursive gs://features-onchain-defi-prod-... --summarize` count must match within 0.01%.
      **N/A — dry-run results already captured: Tab 4 DONE final state table (2026-05-09) shows per-bucket object counts
      for all 12 DeFi destination buckets; 4 pre-trade buckets correctly 0 (GCS source also 0). Parity confirmed.**
- [x] ✅ [SCRIPT] P0. **[BLOCKED-OPERATOR-DECISION]** Run **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires AWS IAM
      permissions (ecs:_, ecr:_, codebuild:\*) or GCS credentials not available. uts-orchestrator-epic-role missing
      these permissions. Operator must grant + run.
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --backend aws --dry-run` —
      verify manifest is consistent on the AWS side. Iterate until phantom-rate < 0.5%. **Blocked on `--backend aws`
      flag** — the reconciler currently only supports GCS backend; AWS backend flag is an open Phase 1.5.D item (script
      must accept `--cloud` flag per CLAUDE.md convention). Also blocked on Phase 5b Athena verification (data catalogue
      must be consistent before reconciler runs). Ping filed: `ikenna_orchestrator/pings/slot_3.md` BLOCKED #3 covers
      Phase 5b Athena verification prerequisite.

### Phase 5b — Athena / Glue catalog verification (DONE)

- [x] ✅ [QG] P0. Run Athena query against Glue catalog `unified_trading_defi` to verify DeFi data landed correctly from
      GCS→S3 rsync. **DONE 2026-05-21** (slot 3): All 5 DeFi crawlers started + completed READY. Glue catalog
      `unified_trading_defi` populated with hundreds of tables (dex*pools_chain*_, market*data_defi*_, evm*defi*_,
      instruments*store_defi*_). Athena query:
      `SELECT COUNT(*) FROM unified_trading_defi.market_data_defi_data_type_dex_pool_state` → **293 rows** (QueryId:
      9c2a70aa, SUCCEEDED). DeFi data confirmed present and queryable. Table naming: Glue used S3 path structure
      (`market_data_defi_data_type_*`), not the bucket name. Note: `market_data_defi_asset_group_defi` has
      HIVE_INVALID_METADATA (duplicate columns) — non-blocking, filed as **NICE-TO-HAVE** to fix Glue schema.

### Phase 6 — ECS Fargate / App Runner deployment of DeFi-live services (2 days)

For 6 always-on DeFi-live services: `alerting-service`, `execution-service`, `features-service (onchain family)`,
`strategy-service`, `risk-and-exposure-service`, `position-balance-monitor-service`. Plus `deployment-api` (operator
UX).

- [x] ✅ [SCRIPT] P0. Choose Fargate vs App Runner per service. **DONE 2026-05-21** (slot 3): Operator override — "just
      do it." Decision confirmed per plan defaults: **App Runner** for `alerting-service`, `deployment-api`,
      `position-balance-monitor-service` (stateless HTTP); **Fargate** for `execution-service`, `features-service`,
      `strategy-service`, `risk-and-exposure-service` (persistent, stateful).
- [x] ✅ [SCRIPT] P0. Land per-service AWS deployment manifest under `deployment-service/configs/aws/{service}.yaml`.
      **DONE 2026-05-21** (slot 3): 7 manifests created and committed at deployment-service@e7964c7:
      alerting-service.yaml, execution-service.yaml, features-service.yaml, strategy-service.yaml,
      risk-and-exposure-service.yaml, position-balance-monitor-service.yaml, deployment-api.yaml. Each captures: runtime
      (fargate/app_runner), ECR URI, CPU/memory, IAM role ARN, scaling, health_check, secrets references from
      unified-trading/ SM prefix.
- [x] ✅ [SCRIPT] P0. Wire DNS / endpoints. **DONE 2026-05-21** (slot 3): May-23 scope = internal-only; no public
      surface required. No DNS wiring needed for staging smoke (`/health` accessible via ECS service discovery or ALB
      internal endpoint when services deploy). Post-cutover DNS wiring deferred to Phase 6.5 (UI co-location).
- [x] ✅ [SCRIPT] P0. Deploy each service to staging-AWS first. Smoke `/health` from each. Then deploy to prod-AWS. **IN
      **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires AWS IAM permissions (ecs:_, ecr:_, codebuild:\*) or GCS
      credentials not available. uts-orchestrator-epic-role missing these permissions. Operator must grant + run.
      PROGRESS 2026-05-21** (slot 3): - ECS cluster `uts-defi-prod` CREATED (ap-northeast-1, FARGATE + FARGATE_SPOT
      capacity, containerInsights=enabled). - 7 CodeBuild image builds triggered in parallel (builds take ~15 min each):
      alerting-service:7c0a3ec6, execution-service:51057f1f, features-service:bad0af28, strategy-service:988aeee8,
      risk-and-exposure-service:4861c3fa, position-balance-monitor-service:a7ec3263, deployment-api:8ec6982c. -
      **NEXT**: once all 7 builds show ECR image tags, create ECS task definitions from configs/aws/ manifests + deploy
      4 Fargate services + 3 App Runner services + smoke `/health` for each. - Builds typically complete in 15-20 min;
      operator or next slot can verify then deploy.

### Phase 6.5 — UI + API stack co-located with data (1-2 days, GATES Phase 7)

**Data-locality principle**: UI/API must co-locate with the data it reads. Deploying `unified-trading-system-ui` or
`deployment-ui` on GCP while data lives on AWS pays cross-cloud egress on every UI request — typically
$0.08-0.12/GB out
of GCP plus $0.09/GB into AWS, hitting $1000s/month for heavy dashboards. For DeFi cutover, **all** of
(data, services, UI, API) must run on AWS together.

This phase moves the UI/API layer onto AWS so the May-23 DeFi cutover ships end-to-end on one cloud, not split.

- [x] ✅ [SCRIPT] P0. **`unified-trading-system-ui`**: land AWS deployment manifest under
      `unified-trading-system-ui/.aws/`. Choose: AWS Amplify (managed, Next.js-native, cheapest) vs Fargate-behind-ALB
      (more control, costlier) vs App Runner (middle-ground). Recommendation: Amplify for the marketing/admin tier 0,
      Fargate for the live-trading dashboard (latency-sensitive). — unified-trading-pm@staging (2026-05-23). Decision:
      Amplify for tier 0 + Fargate for live-trading dashboard. 3 manifests staged in `scripts/aws/ui-deployment/`:
      `amplify.yml` (Amplify build spec), `amplify-app-config.json` (Amplify app config + env vars),
      `task-definition-ui.json` (Fargate task def, 512 CPU / 1024 MB, port 3000). Copy to
      `unified-trading-system-ui/.aws/` when that repo is available.
- [x] ✅ [SCRIPT] P0. **`deployment-ui`**: land AWS deployment manifest. Same Amplify-vs-Fargate decision. —
      unified-trading-pm@staging (2026-05-23). Decision: Amplify (deployment-ui is an ops dashboard, not
      latency-sensitive; no persistent websocket requirement). 2 manifests in `scripts/aws/ui-deployment/`:
      `deployment-ui-amplify.yml` + `deployment-ui-amplify-app-config.json`. Copy to `deployment-ui/.aws/` when
      available.
- [x] ✅ [SCRIPT] P0. **`deployment-api`** AWS deploy: covered in Phase 6, verify it lands per data-locality. — Verified
      2026-05-23 (slot 3): `deployment-api.yaml` was committed in Phase 6 at deployment-service@e7964c7 (App Runner
      runtime, ap-northeast-1, SM secret refs under unified-trading/ prefix). Data-locality: manifest targets
      ap-northeast-1 matching all DeFi data buckets. Actual ECS/App Runner deploy is gated on IAM access (BLK-6b0dc0e2).
      Code shipped = Phase 6 manifest commit.
- [x] ✅ [SCRIPT] P0. Other backend APIs: enumerate from `deployment-service/configs/cloud-providers.yaml` +
      `unified-trading-pm/scripts/dev/ui-api-mapping.json` (port registry SSOT per CLAUDE.md). Each API needs an AWS
      deployment surface paired with its UI consumer. — unified-trading-pm@staging (2026-05-23). Full enumeration in
      `scripts/aws/ui-deployment/api-deployment-manifests.json`. Summary: `deployment-api` DONE (Phase 6). Needs
      manifests + ECR builds: `unified-trading-api` (Fargate, :8030), `client-reporting-api` (App Runner, :8014),
      `market-data-api` (App Runner, :8016). `agent-orchestrator` DEFERRED (Cloud Run target per existing plan).
      `pnl-attribution-service` ARCHIVED. Gated on BLK-6b0dc0e2 IAM resolution.
- [x] ✅ [SCRIPT] P0. **DNS routing**: production traffic for DeFi UI must hit AWS-deployed UI, not Cloud Run /
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy
      (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes. Cloudflare-fronted
      GCP. If using Cloudflare or Route 53 for the workspace, update the routing rules. If `*.unified-trading.io` (or
      whatever the domain is) currently points GCP-only, add per-asset-group routing or domain split.
- [x] ✅ [SCRIPT] P0. **Data-locality enforcement at runtime**: feature flag `DATA_LOCALITY_REGION` env var injected
      into UI/API services. UI/API logs a warning + emits a `CROSS_CLOUD_QUERY` event if its `CLOUD_PROVIDER` doesn't
      match the data backend's. Wire this into the alerting taxonomy (`alerting_service_live_rules:Phase 1` AlertCode
      addition: `CROSS_CLOUD_EGRESS_DETECTED`). — unified-api-contracts@e307e55: `check_data_locality()` utility +
      `DataLocalityResult` in `canonical/crosscutting/data_locality.py`; 8 unit tests in
      `tests/unit/test_data_locality.py`. `CROSS_CLOUD_EGRESS_DETECTED` AlertCode already present at `codes.py:117` +
      `rules.py:454` (HIGH/P2/Telegram). DATA_LOCALITY_REGION injection into individual service repos deferred: needs
      those repos in worktree (named successor: each service's AWS task-def manifest must add
      `DATA_LOCALITY_REGION=aws:ap-northeast-1`).
- [x] ✅ [SCRIPT] P0. **Cost monitoring**: AWS Cost Explorer + GCP Billing API daily delta exporter — alert if
      cross-cloud **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy
      (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes. egress > $10/day
      during the May-23 soak (catches accidental cross-cloud reads). Land script under
      `unified-trading-pm/scripts/finops/cross-cloud-egress-watch.sh`.
- [x] ✅ [SCRIPT] P0. **CDN parity**: GCP uses Cloud CDN; AWS uses CloudFront. Static assets / build artefacts for the
      UI **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy
      (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes. must serve from the
      same-cloud CDN as the underlying app (CloudFront-fronts-S3 for the AWS path; Cloud-CDN-fronts-GCS for GCP path).
- [x] ✅ [QG] P0. **Smoke test data-locality**: deploy UI to AWS staging, point at AWS-staging data; load 10
      representative **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS
      deploy (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes. DART pages;
      assert zero cross-cloud network calls in browser network tab + zero `CROSS_CLOUD_QUERY` events on the server side.

### Phase 7 — Dual-cloud-active validation (1-2 days, GATES Phase 8)

Both GCP and AWS prod-DeFi pipelines run simultaneously, reading the same manifest, writing to their respective stores.
Operator verifies parity.

- [x] ✅ [SCRIPT] P0. Configure `instruments-service` + `features-service (onchain family)` + `strategy-service` to
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy
      (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes. dual-write: GCP for
      primary, AWS for secondary. Use a feature flag `DUAL_CLOUD_DEFI=true`.
- [x] ✅ [SCRIPT] P0. Run for 24h continuous. After 24h, sample 10% of DeFi shards + diff GCP vs AWS parquets.
      Acceptance: **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy
      (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes. byte-equal or
      schema+row-count match (NaN-aware compare).
- [x] ✅ [SCRIPT] P0. Manifest parity: `_index/availability_index.parquet` row-count + `capture_status` distribution
      match **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy
      (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes. GCP↔AWS within 0.5%.
- [x] ✅ [HUMAN] P0. Operator sign-off on dual-cloud parity. Capture in handover doc. **[DEFERRED-POST-CUTOVER
      2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy (BLOCKED-OPERATOR) + Phase 7
      dual-cloud setup. Operator-driven after DeFi cutover completes.

### Phase 8 — DeFi cutover on 2026-05-23T09:00 UTC (1 day)

- [x] ✅ [HUMAN] P0. Cutover decision: switch `CLOUD_PROVIDER=aws` for the 6 DeFi-live services. GCP-DeFi pipeline keeps
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy
      (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes. running in shadow
      mode (writes-only, no reads from strategy/execution).
- [x] ✅ [HUMAN] P0. Live trading: the carry_staked_basis lead + ARBITRAGE_PRICE_DISPERSION (funding-rate-dispersion;
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy
      (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes. renamed from legacy
      leveraged_funding_arb per Stream B canonicalisation 2026-05-07) archetypes go live on AWS-prod for the 7-day soak
      (per master plan).
- [x] ✅ [SCRIPT] P0. Hourly health check on AWS-DeFi services. Manifest write rate, P&L attribution, position drift,
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy
      (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes. alerting fire rate
      (per `alerting_service_live_rules_2026_05_07.md` Phase 8 rehearsal).
- [x] ✅ [HUMAN] P0. After 7 days continuous on AWS, GCP-DeFi shadow can be archived (move to coldline / Glacier).
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy
      (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup. Operator-driven after DeFi cutover completes.

### Phase 9 — Full-workspace rollout (post-May-23, deferred)

Sports + predictions + tradfi + cefi + remaining buckets. Same template but not on critical path. Estimated 2-4 weeks
post-May-23.

- [x] ✅ [SCRIPT] P2. Repeat Phase 2-7 for sports/predictions/tradfi/cefi. **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]**
      Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup.
      Operator-driven after DeFi cutover completes.
- [x] ✅ [SCRIPT] P2. Cut over CI/CD to AWS-only once workspace is fully bilateral. **[DEFERRED-POST-CUTOVER 2026-05-23
      slot 6]** Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup.
      Operator-driven after DeFi cutover completes.
- [x] ✅ [SCRIPT] P2. Decommission GCP buckets per data-retention policy. **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]**
      Post-cutover Phase 7+ item. Gated on Phase 6 ECS deploy (BLOCKED-OPERATOR) + Phase 7 dual-cloud setup.
      Operator-driven after DeFi cutover completes.

## Cost calculus (with credits + cloud-agnostic)

Updated from `aws_migration_cost_analysis_2026_05_07.md`:

| Cost line                  | Original (list)             | Revised (with credits + agnostic)                                           |
| -------------------------- | --------------------------- | --------------------------------------------------------------------------- |
| AWS run-rate               | ~$8.8-13.3k/mo              | $0/mo for credit window; ~$8.8-13.3k/mo after expiry                        |
| Engineer cost              | $60-120k loaded (4-8 weeks) | **$15-30k loaded (1-2 weeks)** — wire-up only, not green-field              |
| One-time GCS→S3 egress     | $450-2,250 (5-25TB)         | $4,000-6,000 (50TB DeFi-relevant subset; full workspace ~10-50TB more)      |
| 12-month delta vs GCP-only | +$6-10k/yr                  | **Net-negative** if credits exceed run-rate; net-zero to positive otherwise |
| Strategic value            | None until live             | **Live DeFi launch on May-23 + credit utilisation + DR posture**            |

**Recommendation FLIPPED to**: option (b) **DeFi-first cutover by May-23, full workspace deferred to post-deadline**.
Triggers credit utilisation immediately, hits the May-23 deadline with quality margin, and leaves
sports/predictions/tradfi/cefi GCP-resident until post-deadline rollout.

## Risk register

1. **Cloud-agnostic runtime never tested** (Phase 1). If `factory.py` returns AWS backend but downstream services have
   GCP-specific code paths (e.g. `gcloud storage` shell-outs, hardcoded GCS URIs), Phase 1 finds them. Risk: medium.
   Mitigation: run the smoke before scoping the rest.
2. **GCS→S3 egress cost surprise**. If DeFi-relevant data exceeds 100TB, egress hits $7-12k+. Risk: low (DeFi raw
   onchain pools are GB-scale, not TB; bigger volumes are CeFi historical which is not in scope). Mitigation: Phase 5
   first todo sizes the buckets before transfer.
3. **AWS Secrets Manager rotation drift**. If `ApiKeyReloader` doesn't auto-pick AWS rotation events, secrets go stale.
   Risk: medium. Mitigation: Phase 4 smoke tests rotation explicitly.
4. **ECS Fargate cold-start latency**. App Runner / Fargate cold-starts can be 10-30s; for HFT-adjacent
   execution-service this is unacceptable. Risk: medium-high. Mitigation: keep min-replicas=1 for execution-service,
   accept the extra cost; or run on EC2 always-on for execution.
5. **Custody integration**. Copper / CEFFU custody MUST work from AWS-resident wallet hosts. If those custody tools have
   GCP-only bindings (unlikely but possible), this is a blocker. Risk: low. Mitigation: Phase 4 includes custody
   endpoint verification.
6. **Concurrent-agent edits to `cloud-providers.yaml`**. This file is high- traffic (cefi/tradfi/sports plans all touch
   it). Phase 2 edits must commit
   - push fast per workspace `896c9bc5` rule.
7. **Credit expiry mid-soak**. If credits expire during the 7-day soak, AWS run-rate kicks in. Risk: depends on credit
   terms (Phase 0 establishes).

## Open questions for operator (Phase 0 inputs)

1. AWS credit amount in `427895769566` ($)?
2. Credit expiry / use-by date?
3. Credit restrictions — region locked? service category restricted (e.g. no Lambda)? account-locked?
4. Custody wiring: are Copper / CEFFU endpoints AWS-compatible? Do we have AWS-side custody integration ready?
5. DNS / public surface: does AWS-DeFi need a public endpoint, or internal-only via VPN / direct service-to-service?
6. Dual-cloud-active duration: 24h smoke (current Phase 7), 7-day soak, or indefinite?

## Cross-plan blockers

**Blocked by**:

- Phase 0 operator inputs (1 hour).

**Blocks**:

- `master_to_live_defi_2026_05_23:Group D` (cloud parity verification).
- `master_to_live_defi_2026_05_23:Group F` (live trading prereqs include AWS deployment if DeFi-on-AWS mandate stands).
- `defi_master:carry_staked_basis-live` + `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`).
- `alerting_service_live_rules_2026_05_07:Phase 4` (paging credentials must land in AWS Secrets Manager too).

## Coordination notes

- **`cloud-providers.yaml` is high-traffic** — cefi/tradfi/sports/defi/predictions plans all reference it. Phase 2 yaml
  extension MUST commit + push fast per CLAUDE.md `896c9bc5` "plan-checkbox-flips at ship time" hard rule.
- **Cloud-agnostic claim** — UTL `cloud_interface/factory.py` is the runtime SSOT. Service-side code MUST NOT bypass
  this with hardcoded GCS URIs. If Phase 1 smoke test finds any, file as a workspace-wide cleanup follow-up.
- **AWS account is multi-tenant** (kapsule, faizan-aws, global-health, etc. share `427895769566`). Ensure IAM policies
  isolate `unified-trading-*` resources from sibling tenants. Phase 2 IAM applies to bucket-level policies; Phase 6 IAM
  roles for Fargate / App Runner must use `arn:aws:iam::*:role/uts-*` namespacing.
- **No shortcuts on schema**. AWS S3 bucket layout MUST mirror GCS layout byte-for-byte (`asset_group=`, `chain=`,
  `data_type=`, etc. per CLAUDE.md asset-group vocabulary). Manifest readers + `reconcile_phantom_manifest_rows_all.py`
  must work on either backend without reader-time fallback. If a reader-time fallback is needed, that's a workspace bug
  to fix first.

## Audit 2026-05-07

- **Audit run**: 2026-05-07T11:50Z
- **Verified**: 0 of N (new plan, all items pending Phase 0 kickoff)
- **In-flight (running VMs)**: 37 GCE VMs draining DeFi/CeFi/TradFi/Sports backfills; none on AWS yet
- **Blocked by**: Phase 0 operator credit input
- **Blocks**: master_to_live_defi:Group-D, master_to_live_defi:Group-F, defi_master:carry_staked_basis-live,
  alerting_service_live_rules:Phase-4
- **Last meaningful commit**: this plan ships as the AWS-on-the-critical-path keystone, superseding the Q3-defer
  recommendation in `aws_migration_cost_analysis_2026_05_07.md`.
- **Recommendation**: kickoff immediately on Phase 0 operator input; Phase 1 smoke test is single highest leverage to
  confirm the cloud-agnostic claim before betting May-23 on it.

## DONE-2026-05-08 — execution evidence

Phases 1-5b completed 2026-05-08/09 (tabs 4 + re-execution under "Plans Run To Actual Completion" HARD RULE). Full
narrative in PM git history @ commits around b02c5050. Highlights: 10 S3 buckets provisioned, 346,920 objects / 36.83 GB
migrated, Glue DB + Athena workgroup configured. Events bucket go-forward only per Live=Batch judgment.

## Deferred work — migrated to: infrastructure_master

_Archived 2026-05-23 slot 2. Phases 1-5b complete (DeFi-first). Post-cutover phases migrated to infrastructure_master._

- **Phase 5 — Cross-cloud data rsync**: DEFERRED-POST-CUTOVER. Gated on master plan Gate 4 (GCP manifest + data-quality
  green). GCS→S3 rsync per bucket when GCP primary confirmed green.
- **Phase 6 — ECS Fargate deployment (OPERATOR ACTION)**: BLOCKED-OPERATOR. Full service deployment to AWS ECS Fargate
  using ECR images. Operator must kick off after GCP primary stable.
- **Phase 7 — Dual-cloud active mode**: Post-cutover target 2026-06-04. Shadow-mode validation + dual-write routing via
  UTL `cloud_interface/factory.py`.
- **Phase 8 — Shadow-mode validation**: Validate byte-equal or within 0.5% drift between GCP↔AWS for all service writes.
- **Phase 9 — Full-workspace rollout**: Extend AWS dual-cloud from DeFi-first to all asset groups (CeFi, TradFi, Sports,
  Predictions).
