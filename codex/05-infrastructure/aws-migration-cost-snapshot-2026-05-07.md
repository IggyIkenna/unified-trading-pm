---
doc_type: codex-ssot
title: AWS migration cost snapshot — 2026-05-07
summary:
  Steady-state per-resource GCP-vs-AWS cost reference — compute / storage / BigQuery / Pub-Sub / Secret Manager /
  registry / Cloud Run run-rate + one-time migration + 12-month TCO; 2026-Q1 list pricing, AWS not materially cheaper
  (~+5-7%).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    features-service,
    strategy-service,
    unified-trading-library,
    unified-trading-system-ui,
  ]
scope: [admin, engineer]
tags: [cost, migration, infrastructure, aws-migration, storage]
related:
  [
    /codex/04-architecture/cloud-agnostic-migration.md,
    plans/active/aws_migration_defi_first_2026_05_07.md,
    /codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md,
  ]
created: 2026-05-08
authoritative_for:
  [
    AWS-vs-GCP per-resource cost snapshot (compute/storage/BigQuery/Pub-Sub run-rate + one-time migration + 12-month TCO,
    2026-Q1 list pricing),
  ]
referenced_by:
  [
    /codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# AWS migration cost snapshot — 2026-05-07

> [!IMPORTANT] **Recommendation paragraph from the source doc is SUPERSEDED 2026-05-07.** This snapshot extracts the
> per-resource cost tables from
> [`aws_migration_cost_analysis_2026_05_07.md`](../../plans/archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md)
> for ongoing reference; the "defer AWS to Q3 2026" recommendation is replaced by the dual-cloud decision in
> [`plans/active/aws_migration_defi_first_2026_05_07.md`](../../plans/active/aws_migration_defi_first_2026_05_07.md) §
> "Operator answers" + Phase 0. The cost numbers below remain valid as a research artefact (list pricing 2026-Q1).
>
> **Pricing flag**: list pricing as of 2026-Q1, sourced from public pricing pages and workspace invoice snapshots.
> Verify against actuals (GCP billing console + AWS Cost Explorer pricing API) before any commitment.
> Spot/preemptible/Reserved Instance discounts NOT applied unless stated.

This doc is the steady-state per-resource cost reference. The full research narrative (executive summary, GCP↔AWS
service map, risk register, recommendation matrix, calculation appendix) lives in the archived analysis. Operators
needing per-resource numbers for capacity planning / dual-cloud sizing read this snapshot; operators needing the
historical narrative read the archived analysis.

---

## Compute (GCE → EC2)

### Footprint snapshot (2026-05-07)

| Item                                            | Value                                                                                               | Source                                                                   |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Currently RUNNING VMs                           | 24                                                                                                  | `gcloud compute instances list` 2026-05-07                               |
| Audit floor (recent)                            | 37 RUNNING peak                                                                                     | master plan audit `12ce828a`                                             |
| Zone (locked)                                   | `asia-northeast1-c` (Tokyo)                                                                         | every launcher; CLAUDE.md VM Naming Convention                           |
| Machine-type distribution (live snapshot)       | 8× e2-highmem-4, 7× e2-highmem-2, 5× e2-standard-8, 2× e2-standard-2, 1× e2-standard-4, 1× e2-small | live snapshot                                                            |
| Machine-type distribution (launcher hard-codes) | 9× e2-standard-4, 10× e2-standard-2, 2× e2-standard-8, 1× e2-highmem-2                              | grep across `deployment-service/scripts/vm/launch-*.sh`                  |
| VMs created since 2026-04-01                    | 22                                                                                                  | `gcloud compute instances list --filter=creationTimestamp>='2026-04-01'` |
| Boot disk default                               | 30–100 GB pd-balanced (per launcher)                                                                | scripts                                                                  |
| Singleton always-on services                    | watchdog (e2-small) + manifest-consolidator + Cloud Run shared deployment-api                       | live snapshot                                                            |

**Compute hours model**:

- 5 always-on services × 24h × 30d = 3,600 instance-hours/month at small-mid sizes
- Backfill burst: ~25 VMs averaging 12 hours/day × 30d = 9,000 instance-hours/month, weighted toward e2-highmem-4 +
  e2-standard-4
- Effective monthly compute hours: **~12,600**

### Per-machine-type pricing (asia-northeast1 / ap-northeast-1, 2026-Q1 list)

| Type          | GCP $/hr | AWS closest type      | AWS $/hr        |
| ------------- | -------- | --------------------- | --------------- |
| e2-small      | 0.0084   | t3.small              | 0.0240          |
| e2-standard-2 | 0.0671   | t3.medium / m6i.large | 0.0500 / 0.0950 |
| e2-standard-4 | 0.1342   | m6i.xlarge            | 0.1900          |
| e2-standard-8 | 0.2683   | m6i.2xlarge           | 0.3800          |
| e2-highmem-2  | 0.0905   | r6i.large             | 0.1260          |
| e2-highmem-4  | 0.1809   | r6i.xlarge            | 0.2520          |

Weighted blended rate ~$0.10/hr GCP (with SUD); ~$0.103/hr AWS on-demand. Spot/preemptible cuts both by 60–80%. **Use
SUD-blended GCP and Savings-Plan-blended AWS for production estimates.**

---

## Storage (GCS → S3)

| Item                       | Value                                                                                                                                                                                                 | Source                       |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| Buckets total              | 239                                                                                                                                                                                                   | `gcloud storage ls \| wc -l` |
| Non-test/dev buckets       | 162                                                                                                                                                                                                   | filter `-test-`/`-dev-`      |
| Major data bucket families | events, market-data-tick-{cefi,defi,tradfi,sports,prediction}, features-{delta-one,onchain,volatility,calendar}-{asset_group}, execution-store-{cefi,defi,tradfi}, sports_reference, instruments_data | bucket listing               |

**Estimated storage scale** (assumption-flagged — GCP `du -s` per-bucket times out without a same-region worker;
workspace memory cites "35GB roots" per CeFi spot/perp instrument as the source atom):

| Bucket family                                                               | Estimated GB    | Reasoning                                                                                                                    |
| --------------------------------------------------------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Raw tick (CeFi+TradFi+DeFi+Sports+Prediction)                               | 8,000–15,000 GB | CeFi spot/perp ~35GB/instrument × ~50 instruments × multi-year + bundled options/futures + sports per-fixture odds histories |
| Features (delta-one + onchain + volatility + calendar + sports + commodity) | 2,000–4,500 GB  | Per-asset-group computed parquets, ~100 feature_groups × 5 asset_groups                                                      |
| Events (audit log JSONL)                                                    | 200–500 GB      | per-VM hourly partitions, growing daily                                                                                      |
| Execution-store + backtest-results + ml-models + ml-predictions             | 500–1,500 GB    | strategy + ML output                                                                                                         |
| Deployment scripts + data-status-rollups + config + misc                    | <100 GB         | small ops buckets                                                                                                            |
| **Total**                                                                   | **~11–22 TB**   | midpoint **~16 TB** for cost modelling                                                                                       |

Region: vast majority `asia-northeast1` (Tokyo) Standard class. A few legacy buckets live in `europe-west1` (Cloud Run
side-services) and `us-central1` / `us-multi-region` (firebase/odum-portal).

**Per-GB pricing (2026-Q1 list)**:

- GCS Standard asia-northeast1: $0.026/GB/mo
- S3 Standard ap-northeast-1: $0.024/GB/mo
- 16 TB midpoint × 1024 = 16,384 GB
- GCS: $426/mo; S3: $393/mo

---

## BigQuery → Athena+Glue

| Item                        | Value                                                                                                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Datasets                    | 24 (`market_data`, `market_tick_asia`, `features`, `ml_models`, `ml_predictions`, `sports_analytics`, `sports_betting`, `execution_logs`, `audit`, `billing`, etc.) |
| Region                      | `asia-northeast1`                                                                                                                                                   |
| Usage pattern               | secondary analytics layer — primary data store is GCS parquet; BQ holds curated/aggregated views + sim-results                                                      |
| Estimated active table size | <2 TB total (heuristic; primary data lives in GCS)                                                                                                                  |
| Query volume                | ad-hoc analyst queries; no production scheduled query firehose visible                                                                                              |

---

## Pub/Sub → SNS+SQS

| Item                     | Value                                                                                                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Topics                   | 62                                                                                                                                                    |
| Pattern                  | service lifecycle events, fill-events per venue, position-updates, risk-breach-alerts, deployment-status, market-ticks, ml-predictions, signal events |
| Estimated message volume | live-trading not yet at scale; backfill-driven heartbeat events dominate; likely <10M messages/month current, will ramp post-cutover (June 2026+)     |

---

## Secret Manager → AWS Secrets Manager

| Item    | Value                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Secrets | 140                                                                                                                            |
| Pattern | venue API keys (CeFi exchanges, DeFi RPC keys, Tardis, Databento, sports providers), wallet private keys, OAuth client secrets |

---

## Artifact Registry → ECR

| Item               | Value                                                                                                                                                                                                                                                                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Repos              | 57 Docker repos (`unified-trading-library`, `execution`, `strategy-service`, `ml-training-service`, `features-*-service`, …)                                                                                                                                                                                                       |
| Total size         | **608 GB** (`sizeBytes` field is megabytes per gcloud output)                                                                                                                                                                                                                                                                      |
| Top consumers (MB) | cloud-run-source-deploy 178k + 23k + 11k, unified-trading-system 137k, unified-trading-library 73k, execution 30k, strategy-service 24k, ml-training-service 21k, features-service (volatility family) 16k, features-service (onchain family) 13k, features-service (calendar family) 12k, features-service (delta-one family) 11k |

---

## Cloud Run + Cloud Functions → Fargate / App Runner / Lambda

| Service                                                                   | Region                                       | Notes                                                                                |
| ------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------ |
| `uts-shared-deployment-api`                                               | asia-northeast1                              | hot-path; 5+ min query latency before 2026-05-06 slicer fast-path; now <2s in-region |
| `deployment-dashboard`                                                    | asia-northeast1                              | active                                                                               |
| `multi-repo-agent`                                                        | europe-west1                                 | dev tooling                                                                          |
| `odum-portal` (3 regions)                                                 | asia-northeast1 / europe-west4 / us-central1 | marketing                                                                            |
| `signal-broadcast-smoke-receiver`                                         | europe-west1                                 | smoke target                                                                         |
| `visualizer-api` / `visualizer-ui`                                        | asia-northeast1                              | active                                                                               |
| `quota-broker`, `trigger-instruments-job`, `trigger-market-tick-cefi-job` | asia-northeast1                              | event glue                                                                           |
| `central-market-data-tardis-loader`, `run-jobs-tardis-data-loader`        | europe-west1                                 | legacy 2024; likely zero traffic                                                     |
| `market-data-query-service`                                               | asia-northeast1                              | low traffic                                                                          |
| `user-management-api`, `odum-user-mgmt-admin`                             | us-central1                                  | auth admin                                                                           |

Estimate: ~21 Cloud Run services. Most are low-traffic event handlers; a few (deployment-api, dashboard, visualizer,
odum-portal) are hot-path interactive.

---

## Firebase (Identity Platform + Firestore + Storage + Auth + Hosting)

Used for the unified-trading-system-ui authentication tier (Tier 0 emulator suite + staging + prod). Documented across
`/codex/14-customer-journeys/authentication/firebase-local.md` + workspace dev tiers. Auto-included in the GCP project.
Identity Platform pricing kicks in above 50k MAU; Firestore charges per read/write/storage.

---

## Monthly run-rate (mid-band) — GCP vs AWS list pricing

**All numbers are list pricing 2026-Q1; ap-northeast-1 / asia-northeast1.** GCP sustained-use discount (SUD)
auto-applies to GCE; AWS Reserved Instances / Savings Plans NOT applied. Spot-equivalent VMs (GCE preemptible / EC2
spot) NOT modelled — workspace launchers all use on-demand.

| Category                                                      | GCP $/mo               | AWS $/mo               | Delta           | Notes                                                                                         |
| ------------------------------------------------------------- | ---------------------- | ---------------------- | --------------- | --------------------------------------------------------------------------------------------- |
| Compute (12,600 instance-hours/mo)                            | $1,200                 | $1,300                 | +$100 (+8%)     | GCE e2 tier vs EC2 t3/m6i; SUD already in GCP figure                                          |
| GCS / S3 storage (16 TB Standard)                             | $416                   | $384                   | −$32 (−8%)      | S3 Standard $0.024/GB; GCS Standard $0.026/GB asia-northeast1                                 |
| Storage operations (Class A+B requests, 16 TB hot)            | $80                    | $90                    | +$10            | similar order of magnitude                                                                    |
| BigQuery (24 datasets, ~2 TB, modest scan) → Athena+Glue      | $250                   | $180                   | −$70            | Athena $5/TB scanned; assumes 30 TB/mo scan with Glue catalogue overhead $30                  |
| Pub/Sub → SNS+SQS (10M messages/mo)                           | $40                    | $20                    | −$20            | SNS $0.50/M + SQS $0.40/M < Pub/Sub $40/TB                                                    |
| Secret Manager (140 secrets, ~10k reads/mo)                   | $84                    | $84                    | $0              | both ~$0.40/secret/mo + $0.03/10k reads                                                       |
| Artifact Registry / ECR (608 GB)                              | $61                    | $61                    | $0              | both $0.10/GB/mo                                                                              |
| Cloud Run / Fargate (21 services, low traffic)                | $400                   | $500                   | +$100 (+25%)    | Fargate per-vCPU-hour is more expensive than Cloud Run req-based; offset partly by App Runner |
| Cloud Build / CodeBuild (CI builds)                           | $250                   | $200                   | −$50            | CodeBuild slightly cheaper per minute                                                         |
| Cloud Functions / Lambda (~50 small fns)                      | $30                    | $25                    | −$5             | low traffic; both well within free tier on most fns                                           |
| Firestore / DynamoDB (Firebase auth+data)                     | $150                   | $200                   | +$50            | DynamoDB on-demand is competitive but Firestore real-time listeners are subsidized            |
| Identity Platform / Cognito (low MAU)                         | $50                    | $55                    | +$5             | both within free tier for current MAU                                                         |
| Logging / Monitoring (CloudWatch)                             | $200                   | $300                   | +$100           | CloudWatch ingest is famously expensive                                                       |
| Networking / NAT / Egress (intra-region, modest cross-region) | $300                   | $380                   | +$80            | NAT Gateway in AWS is significantly more expensive than Cloud NAT                             |
| **Subtotal (mid-band)**                                       | **~$3,510**            | **~$3,780**            | **+$270 (+8%)** | parity within noise                                                                           |
| Data egress (live trading, modest)                            | $300                   | $400                   | +$100           | AWS internet egress higher per GB above 100 TB tier                                           |
| Backfill burst overhead (variable)                            | +$2,000–$5,000         | +$2,200–$5,500         | +10%            | dominant variable cost                                                                        |
| **Total run-rate (mid-band)**                                 | **~$8,300–$12,500/mo** | **~$8,800–$13,300/mo** | **+5% to +7%**  |                                                                                               |

---

## One-time migration costs

| Item                                                     | Estimated cost       | Notes                                                                                                                                                                                                                |
| -------------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GCS → S3 data migration (16 TB egress)                   | $1,440               | GCS internet egress to AWS asia-northeast1: $0.09/GB × 16,000 GB. Could compress slightly; could use S3 Transfer Family but GCS-side egress dominates                                                                |
| Container image migration (608 GB)                       | $55                  | 608 GB × $0.09/GB GCS egress                                                                                                                                                                                         |
| Secret Manager migration (140 secrets)                   | <$5                  | trivial; manual or script                                                                                                                                                                                            |
| BigQuery dataset export → S3 (~2 TB)                     | $180                 | 2 TB × $0.09/GB                                                                                                                                                                                                      |
| Engineer time (4–8 weeks loaded @ $15k/wk loaded)        | **$60,000–$120,000** | **dominant** one-time cost. Includes per-cloud abstraction in `unified-cloud-interface` (UCI), per-service cloud-agnostic re-test, IAM/Secrets/role port, CI rebuild for AWS targets, dual-cloud QG, runbook updates |
| Tenderly fork / testnet re-validation post-migration     | $5,000               | cycle of integration tests on AWS-backed env                                                                                                                                                                         |
| Buffer (auth tier rebuild Firebase→Cognito if scoped in) | $20,000–$40,000      | only if Firebase migration in-scope; deferrable                                                                                                                                                                      |
| **Total one-time**                                       | **$66,680–$166,680** | mid-band ~$110k                                                                                                                                                                                                      |

---

## 12-month TCO

| Scenario                                         | Compute + storage + ops | One-time   | 12-month total                              |
| ------------------------------------------------ | ----------------------- | ---------- | ------------------------------------------- |
| Stay on GCP                                      | $100,000–$150,000       | $0         | **$100k–$150k**                             |
| Full AWS migration (no Firebase rewrite)         | $106,000–$160,000       | $66k–$130k | **$172k–$290k** year 1, then $106k–$160k/yr |
| Full AWS migration + Firebase→Cognito            | $106,000–$160,000       | $86k–$170k | **$192k–$330k** year 1                      |
| Dual-cloud (GCP primary, AWS DR-only data plane) | $130,000–$190,000       | $20k–$40k  | **$150k–$230k** year 1                      |

**Observation**: AWS list pricing is **not materially cheaper** than GCP for this workload at current scale. The major
levers are RI/Savings Plans commitment (GCP equivalent: CUDs) and architectural choice (Athena vs BQ, Fargate vs Cloud
Run). At current scale neither cloud has a decisive cost edge.

---

## References

- Source research doc (archived):
  [`plans/archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md`](../../plans/archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md)
- Active dual-cloud decision:
  [`plans/active/aws_migration_defi_first_2026_05_07.md`](../../plans/active/aws_migration_defi_first_2026_05_07.md)
- Cloud-agnostic SSOT:
  [`/codex/04-architecture/cloud-agnostic-migration.md`](/codex/04-architecture/cloud-agnostic-migration.md)
- Pricing sources (verify before commitment): GCP pricing pages 2026-01 snapshot, AWS pricing pages 2026-01 snapshot,
  internal billing console.
