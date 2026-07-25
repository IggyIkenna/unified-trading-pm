---
doc_type: plan
title: AWS Migration Cost Analysis — 2026-05-07
summary:
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [alerting-service, deployment-api, deployment-service, strategy-service, unified-trading-library, unified-trading-pm]
scope: [admin, engineer]
tags: []
related: []
created: "2026-05-07"
---

## Status — superseded 2026-05-08 by codex_refactor Phase F.4

This research deliverable was extracted to a per-resource cost snapshot at
[`/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md`](/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md)
and the original moved here for historical reference. The original "defer AWS to Q3 2026" recommendation was superseded
earlier on 2026-05-07 by the dual-cloud decision in
[`plans/active/aws_migration_defi_first_2026_05_07.md`](../../active/aws_migration_defi_first_2026_05_07.md). The
per-resource cost tables remain useful for capacity planning and live-cloud-parity sizing; consult the snapshot for
ongoing reference. Historical narrative (executive summary, GCP↔AWS service map, risk register, recommendation matrix,
calculation appendix) preserved in this archive.

# AWS Migration Cost Analysis — 2026-05-07

> [!IMPORTANT] **Recommendation SUPERSEDED 2026-05-07.** This document's "defer AWS to Q3 2026" conclusion is
> **superseded** by the dual-cloud decision recorded in
> [`plans/active/aws_migration_defi_first_2026_05_07.plan.md`](../../plans/active/aws_migration_defi_first_2026_05_07.plan.md)
> § "Operator answers" + Phase 0 (commit `893a9da4`). The cost-analysis numbers in this doc remain valid as a research
> artefact, but the recommendation paragraph is replaced by: **AWS dual-cloud-active for DeFi + CeFi-instruments by
> 2026-05-23, with sports / predictions / tradfi / cefi-historical staying GCP-resident; Phase 9 dual-write expansion
> post-May-23.**
>
> The bottom-line cost numbers (GCP ~$8.3-12.5k/mo, AWS list ~$8.8-13.3k/mo, +5-7% delta) are NOT load-bearing for the
> May-23 decision because the operator confirmed ≥$40k of AWS credits over 11 months covers the DeFi+CeFi-instr
> run-rate.

> **Status**: research deliverable. Unblocks `master_to_live_defi_2026_05_23.plan.md` work-stream-D (D.1–D.5 AWS↔GCP
> cloud parity). Operator-facing go/no-go input for the May-23 cycle. **Pricing flag**: list pricing as of 2026-Q1,
> sourced from public pricing pages and workspace invoice snapshots. Verify against actuals (GCP billing console + AWS
> Cost Explorer pricing API) before any commitment. Spot/preemptible/Reserved Instance discounts NOT applied unless
> stated.

## Executive summary

The Unified Trading System currently runs on a single GCP project (`central-element-323112`, `asia-northeast1` Tokyo
region). Running snapshot 2026-05-07: 24 GCE VMs, 239 GCS buckets, 24 BigQuery datasets, 62 Pub/Sub topics, 140 Secret
Manager secrets, ~~608 GB Artifact Registry, ~~21 Cloud Run services, ~~50 Cloud Functions (eventarc/firebase glue).
Estimated monthly GCP run-rate is **~~$8,300–$12,500/month** depending on storage growth and concurrent backfill VM
hours. Equivalent AWS deployment in `ap-northeast-1` (Tokyo) lands at **~~$8,800–$13,300/month** — **+5% to +7% on list
pricing**, with a **one-time migration cost dominated by 5–25 TB of cross-cloud egress (~~$450–$2,250) plus 4–8
engineer-weeks (~$60k–$120k loaded)**.

12-month run-rate delta is roughly **+$6k to +$10k/year on list pricing**, well within the noise of sustained-use vs
Reserved discounts (GCP SUD is automatic; AWS RI/Savings Plans require commitment). The decision is therefore **not
cost-driven** — it is driven by the May-23 deadline, custody/regulatory requirements (Copper + CEFFU), and the
engineering opportunity cost of a parity migration vs shipping live DeFi trading.

**Recommendation: option (a) — defer full AWS parity to Q3 2026.** A scoped subset (S3 + Secrets Manager + ECR
data-plane parity) is shippable in 5–7 engineer-days but adds no live-trading capability before May-23 and burns
engineer cycles needed for writegate-honest-coverage Layer 4–5, alerting-service, strategy/execution Group F, and DART.
AWS parity is a Q3 cloud-availability/disaster-recovery deliverable, not a May-23 keystone.

---

## Current GCP usage snapshot (2026-05-07)

### Compute (GCE)

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

**Compute hours model (assumption, citation-flagged)**:

- 5 always-on services × 24h × 30d = 3,600 instance-hours/month at small-mid sizes
- Backfill burst: ~25 VMs averaging 12 hours/day × 30d = 9,000 instance-hours/month, weighted toward e2-highmem-4 +
  e2-standard-4
- Effective monthly compute hours: **~12,600**

### Storage (GCS)

| Item                       | Value                                                                                                                                                                                                 | Source                       |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| Buckets total              | 239                                                                                                                                                                                                   | `gcloud storage ls \| wc -l` |
| Non-test/dev buckets       | 162                                                                                                                                                                                                   | filter `-test-`/`-dev-`      |
| Major data bucket families | events, market-data-tick-{cefi,defi,tradfi,sports,prediction}, features-{delta-one,onchain,volatility,calendar}-{asset_group}, execution-store-{cefi,defi,tradfi}, sports_reference, instruments_data | bucket listing               |

**Estimated storage scale (assumption-flagged — GCP `du -s` per-bucket times out without a same-region worker; workspace
memory cites "35GB roots" per CeFi spot/perp instrument as the source atom)**:

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

### BigQuery

| Item                        | Value                                                                                                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Datasets                    | 24 (`market_data`, `market_tick_asia`, `features`, `ml_models`, `ml_predictions`, `sports_analytics`, `sports_betting`, `execution_logs`, `audit`, `billing`, etc.) |
| Region                      | `asia-northeast1`                                                                                                                                                   |
| Usage pattern               | secondary analytics layer — primary data store is GCS parquet; BQ holds curated/aggregated views + sim-results                                                      |
| Estimated active table size | <2 TB total (heuristic; primary data lives in GCS)                                                                                                                  |
| Query volume                | ad-hoc analyst queries; no production scheduled query firehose visible                                                                                              |

### Pub/Sub

| Item                     | Value                                                                                                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Topics                   | 62                                                                                                                                                    |
| Pattern                  | service lifecycle events, fill-events per venue, position-updates, risk-breach-alerts, deployment-status, market-ticks, ml-predictions, signal events |
| Estimated message volume | live-trading not yet at scale; backfill-driven heartbeat events dominate; likely <10M messages/month current, will ramp post-May-23                   |

### Secret Manager

| Item    | Value                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Secrets | 140                                                                                                                            |
| Pattern | venue API keys (CeFi exchanges, DeFi RPC keys, Tardis, Databento, sports providers), wallet private keys, OAuth client secrets |

### Artifact Registry

| Item               | Value                                                                                                                                                                                                                                                                                          |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Repos              | 57 Docker repos (`unified-trading-library`, `execution`, `strategy-service`, `ml-training-service`, `features-*-service`, …)                                                                                                                                                                   |
| Total size         | **608 GB** (`sizeBytes` field is megabytes per gcloud output)                                                                                                                                                                                                                                  |
| Top consumers (MB) | cloud-run-source-deploy 178k + 23k + 11k, unified-trading-system 137k, unified-trading-library 73k, execution 30k, strategy-service 24k, ml-training-service 21k, features-volatility-service 16k, features-onchain-service 13k, features-calendar-service 12k, features-delta-one-service 11k |

### Cloud Run + Cloud Functions

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

### Firebase (Identity Platform + Firestore + Storage + Auth + Hosting)

Used for the unified-trading-system-ui authentication tier (Tier 0 emulator suite + staging + prod). Documented across
`/codex/14-customer-journeys/authentication/firebase-local.md` + workspace dev tiers. Auto-included in the GCP project.
Identity Platform pricing kicks in above 50k MAU; Firestore charges per read/write/storage.

---

## GCP ↔ AWS service map

| GCP service                               | AWS equivalent                                                             | Migration complexity | Semantic differences                                                                                                                                                                                                                                                                                                                                                                                            |
| ----------------------------------------- | -------------------------------------------------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GCS (Standard)                            | S3 (Standard)                                                              | **Low**              | conditional generation match (`x-goog-if-generation-match`) ↔ S3 conditional puts (`If-Match` ETags); workspace `ManifestWriter` uses GCS-specific CAS. **Codex impact**: writegate-honest-coverage Layer 1 manifest writer needs an AWS abstraction layer or per-cloud branch. Egress + request pricing differs (S3 has more granular tiering).                                                                |
| GCS (lifecycle to Coldline/Archive)       | S3 Glacier Instant / Deep Archive                                          | Low                  | rule equivalents; tier prices differ                                                                                                                                                                                                                                                                                                                                                                            |
| GCE (e2 family)                           | EC2 (t3 / m6i / r6i families)                                              | **Low**              | spot pricing equivalent; AMI building required for each VM tarball image; startup-script semantics map cleanly to user-data                                                                                                                                                                                                                                                                                     |
| GCE persistent disks                      | EBS (gp3 / io2)                                                            | Low                  | gp3 closest to pd-balanced                                                                                                                                                                                                                                                                                                                                                                                      |
| Pub/Sub                                   | SNS + SQS                                                                  | **Medium**           | Pub/Sub pull subscriptions ≈ SQS; push subs ≈ SNS+HTTP. Exactly-once-ish semantics differ (Pub/Sub now has exactly-once delivery; SQS standard is at-least-once). EventArc → EventBridge analog. **Workspace impact**: 62 topics + per-venue fill-events fan-out → manageable but per-topic config porting is tedious.                                                                                          |
| BigQuery                                  | Athena (over S3 parquet) **or** Redshift Serverless                        | **High**             | BQ pricing model is unique (on-demand $/TB scanned + flat-rate slot reservations). Athena is closest semantically (S3-native serverless SQL). Redshift adds management. **Workspace impact**: BQ is a secondary layer; primary data is GCS parquet. Athena over S3 is the natural translation and pricing-competitive. Existing BQ DDL needs porting (BQ-specific functions, partition decorators, clustering). |
| Secret Manager                            | AWS Secrets Manager                                                        | **Low**              | API surface comparable; rotation hooks differ (GCP uses Pub/Sub trigger, AWS uses Lambda invocation). 140 secrets to migrate.                                                                                                                                                                                                                                                                                   |
| Artifact Registry (Docker)                | ECR                                                                        | **Low**              | docker push/pull identical; per-tag lifecycle policies map. **Egress is the bottleneck**: 608 GB image transfer at $0.08–0.12/GB egress = $50–75 one-time.                                                                                                                                                                                                                                                      |
| Cloud Build                               | CodeBuild + CodePipeline                                                   | **Medium**           | Cloud Build YAML → CodeBuild buildspec.yml; per-step substitutions differ. ~21 service repos to re-author.                                                                                                                                                                                                                                                                                                      |
| Cloud Run                                 | Fargate (ECS or App Runner)                                                | **Medium**           | Cloud Run is closer to App Runner (HTTPS-native, scales-to-zero); Fargate task-definition is heavier. Cold-start latencies differ. Existing services use Cloud Run env-var injection + service identity; AWS uses task IAM roles.                                                                                                                                                                               |
| Cloud Functions (eventarc/firebase glue)  | Lambda                                                                     | Low–Medium           | mostly used as glue between Pub/Sub topics + Firestore. Rebuilding 50 small functions is mechanical.                                                                                                                                                                                                                                                                                                            |
| Firestore                                 | DynamoDB **or** DocumentDB                                                 | **High**             | Firestore is document + real-time-listener; DynamoDB is key-value with no native listeners (need DynamoDB Streams + Lambda or AppSync). DocumentDB is MongoDB-compatible but no real-time. **Workspace impact**: Tier 0 dev emulator suite tightly coupled to Firebase SDK; rewriting auth tier is days, not weeks.                                                                                             |
| Identity Platform / Firebase Auth         | Cognito                                                                    | **High**             | OAuth flows + custom claims map but token formats + admin SDK calls differ; passwordless + MFA wiring is rebuild work. **Workspace impact**: unified-trading-system-ui authenticates against Firebase; full UI auth path needs migration.                                                                                                                                                                       |
| Cloud DNS                                 | Route 53                                                                   | Low                  | record-by-record port                                                                                                                                                                                                                                                                                                                                                                                           |
| Cloud Logging / Monitoring                | CloudWatch Logs / CloudWatch Metrics                                       | Medium               | log structure differs; alert rules port                                                                                                                                                                                                                                                                                                                                                                         |
| Cloud Build Triggers (GitHub integration) | CodeBuild + CodePipeline + GitHub source action **or** keep GitHub Actions | Low                  | most workspace CI runs in GitHub Actions already; only GHA + per-repo `cloudbuild.yaml` needs porting                                                                                                                                                                                                                                                                                                           |

**No clean equivalent**: BigQuery's combined storage + query model. Athena+Glue is the closest workflow, but BQ's unique
features (table snapshots, ML built-in, federated queries, INFORMATION_SCHEMA) require either Redshift or app-side
replacement.

---

## Cost comparison table (12-month TCO)

**All numbers are list pricing 2026-Q1; ap-northeast-1 / asia-northeast1.** GCP sustained-use discount (SUD)
auto-applies to GCE; AWS Reserved Instances / Savings Plans NOT applied. Spot-equivalent VMs (GCE preemptible / EC2
spot) NOT modelled — workspace launchers all use on-demand.

### Monthly run-rate (mid-band assumption)

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

### One-time migration costs

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

### 12-month TCO

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

## Risk register

| #   | Risk                                                                                                                                                                                                                                                                                                                                                                     | Severity            | Mitigation                                                                                                                                                                                                                      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **GCS → S3 manifest CAS semantics** — `ManifestWriter` uses GCS conditional generation match. S3 conditional puts use ETags + `x-amz-copy-source-if-match`, but consistency model differs (S3 is now strongly consistent for new objects, but multi-region replication has eventual consistency). Per-VM shard isolation rule (CLAUDE.md) MUST be re-validated under S3. | High                | Phase 1 of any migration: write contract tests in `unified-cloud-interface` covering CAS round-trips; per-cloud `record_captured` test matrix.                                                                                  |
| 2   | **Pub/Sub at-least-once vs SNS+SQS exactly-once-ish** — 62 topics include fill-events per venue (exactly-once matters for position state) and risk-breach-alerts. Pub/Sub recently shipped exactly-once delivery; AWS SQS FIFO offers ordered exactly-once but is single-AZ. Re-architecting fill-event topology may be required.                                        | High                | Audit each topic; classify into "exactly-once required" (fill-events, position-updates, eod-settlement) vs "at-least-once OK" (heartbeats, lifecycle events). FIFO SQS for the former; Standard SQS for the latter.             |
| 3   | **Tokyo region pinning** — workspace requires asia-northeast1 for crypto venue latency (Bybit, Binance, OKX, Hyperliquid). AWS ap-northeast-1 (Tokyo) exists and offers comparable peering. Latency profile to Bybit/Binance/Deribit unchanged in practice. **Validate before commitment**.                                                                              | Medium              | Run latency probes from EC2 ap-northeast-1 to each venue WS endpoint; compare to GCE asia-northeast1-c. Acceptance criterion: median ≤ 30ms each venue.                                                                         |
| 4   | **Egress cost during migration** (~$1,440 for 16 TB GCS→S3) — if storage doubles between estimate and execution, cost doubles. Backfill activity since estimate could push to 20+ TB.                                                                                                                                                                                    | Medium              | Pre-flight: actual `du -s` per bucket from in-region GCE worker before launching migration. Use Storage Transfer Service (lower egress fees than direct download).                                                              |
| 5   | **BigQuery → Athena translation** — BQ-specific features (geospatial, ML inline, federated, table snapshots) have no Athena equivalent. Workspace usage is moderate but `tardis_femi` and `aethergate_analytics` datasets may have BQ-specific DDL.                                                                                                                      | Medium              | Audit DDL per dataset; flag BQ-isms. Athena+Glue covers ~85% of typical analytics; remaining 15% needs Redshift or app-side.                                                                                                    |
| 6   | **Firebase Identity Platform → Cognito** — auth flow rewrite touches every UI service that authenticates. Tier 0 emulator suite is Firebase-specific.                                                                                                                                                                                                                    | High (if scoped in) | **Scope OUT** of any May-23 migration. Auth tier stays on Firebase indefinitely; AWS migration covers data + compute only. Firebase project survives independently.                                                             |
| 7   | **Cloud Build → CodeBuild ergonomics** — GHA already does most CI; per-repo `cloudbuild.yaml` is the gap. ~21 services × 1 yaml each = mechanical port but tedious.                                                                                                                                                                                                      | Low                 | Lift-and-shift to CodeBuild buildspec.yml; or skip entirely if GHA + ECR push covers the build path.                                                                                                                            |
| 8   | **Secret Manager rotation hooks** — workspace `ApiKeyReloader` (UTL) reads from GCP SM via Pub/Sub-triggered invalidation. AWS SM uses Lambda-triggered rotation. UTL needs a per-cloud reloader implementation.                                                                                                                                                         | Medium              | Branch on `CLOUD_PROVIDER` env in `unified-cloud-interface`; each cloud's reloader is ~100 LOC. Already covered partially by existing UCI abstraction.                                                                          |
| 9   | **No fire-and-forget VM launches rule** (CLAUDE.md) — events stream to `gs://{pid}-events/`. AWS analog is `s3://{pid}-events/`. EventArc → EventBridge for the streaming layer. Production observability rule needs AWS-equivalent enforcement.                                                                                                                         | Medium              | Add `events_bucket_for_provider()` helper in UCI; verify-launch script accepts both.                                                                                                                                            |
| 10  | **Manifest concurrency principle** (read-once + per-date freshness check + write-time CAS) — depends on cloud-specific atomic operations. S3 ETag CAS is well-documented; Pub/Sub→SQS migration breaks the manifest-consolidator daemon's signalling pattern.                                                                                                            | High                | Consolidator daemon is a singleton; rewrite to poll S3 `_index/per_vm/` + write canonical with CAS. Validate with the workspace dual-vocab probe utility from UTL `manifest_audit`.                                             |
| 11  | **Two clouds = double surface area** (dual-cloud approach) — UCI grows two implementations of each cloud-touching helper. Test matrix doubles. Bandit/QG passes per-cloud.                                                                                                                                                                                               | Medium              | If pursued, accept the QG cost as the price of cloud-agnostic. Existing UCI design already anticipates this; the codex doc `cloud-agnostic-migration.md` (currently a placeholder pointing to architecture/) is the right home. |
| 12  | **Data residency / regulatory** — Copper + CEFFU custody (May-23 keystone) likely has no AWS preference, but check before commitment.                                                                                                                                                                                                                                    | Low                 | Confirm with Copper + CEFFU integration teams; both are venue-agnostic for cloud.                                                                                                                                               |

---

## Recommendation

### Decision matrix

| Option                                              | Description                                                                                                                                                                | Engineering cost (FTE-weeks to May-23)  | Risk to May-23 deadline                                       | 12-month $ delta vs status-quo           | Recommended?                                          |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------- | ---------------------------------------- | ----------------------------------------------------- |
| (a) **Defer AWS parity post-May-23**                | AWS migration becomes a Q3 deliverable. Treat May-23 as GCP-only. Update `master_to_live_defi_2026_05_23.plan.md` to mark D.1–D.5 as "deferred Q3 2026 — see this report". | 0                                       | None                                                          | $0 (status quo)                          | **GO**                                                |
| (b) **AWS dual-target by May-23 (data plane only)** | S3 + Secrets Manager + ECR mirrored from GCP nightly. No compute on AWS. UI/auth stays Firebase. Useful as cold-DR substrate.                                              | 5–7 weeks                               | Medium — eats writegate Layer 4–5 + alerting-service capacity | +$20k one-time, +$1k/mo run-rate         | **NO-GO** for May-23; reconsider as Q3 stepping-stone |
| (c) **Full AWS parity by May-23**                   | Compute, storage, secrets, CI all migrated; UI auth ported Firebase→Cognito.                                                                                               | 10–16 weeks (does not fit the calendar) | **Critical — would forfeit May-23 deadline**                  | +$130k one-time, +$3k/mo run-rate year 1 | **NO-GO**                                             |

### Go decision (one-line per option)

- **(a) Defer to Q3 2026** — **GO**. Recommended.
- **(b) AWS dual-target data plane by May-23** — **NO-GO**. Schedule risk > parity benefit pre-deadline.
- **(c) Full AWS parity by May-23** — **NO-GO**. Calendar-infeasible.

### Rationale

1. **Cost is not the driver**. AWS list pricing is +5%–+7% vs GCP at current scale. Neither cloud delivers a meaningful
   cost edge until traffic scales 5–10×. RI/Savings Plans on AWS could close the gap; CUDs on GCP could open it. Net:
   cost-neutral within noise.
2. **May-23 keystone unblocks are elsewhere**. Per the master plan audit (`12ce828a`), the three keystones are:
   writegate Layer 4–5 (5 reconcilers + reader-side fallback), alerting-service plan + Group F trading guardrails, and
   Copper/CEFFU custody. AWS parity is named in work-stream-D but is the LEAST tightly coupled to "live DeFi trading on
   a real wallet ≥7 continuous days".
3. **Engineering opportunity cost dominates**. 4–8 engineer-weeks for a partial migration is the same envelope as
   shipping the writegate Layer 4 reconcilers (ai/`writegate_honest_coverage_endtoend_2026_05_06.plan.md`) PLUS the
   alerting-service plan PLUS strategy/execution Group F. Trade is uneven.
4. **AWS as DR substrate is a Q3 win, not May-23**. Once the deadline ships, the dual-cloud story becomes about disaster
   recovery + regulatory diversification, both of which are post-MVP concerns and can be staged at planned cadence
   rather than crash-priority.
5. **Doc coverage already exists** for the cloud-agnostic abstraction layer. UCI was designed for per-provider
   switching; emulator suite already exercises the GCS+Pub/Sub+BQ paths via fsouza/moto in tests. The pluggability is in
   place; only the AWS implementations are missing. This is a tractable Q3 effort.

### What to do at the master plan level

1. Update `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.plan.md` work-stream-D items D.1–D.5: change
   status from "BLOCKED awaiting cost analysis" to "deferred Q3 2026 — see
   `/codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md`". Cite this report.
2. Open a successor plan stub in `unified-trading-pm/plans/ai/` named `aws_migration_q3_2026.plan.md` with the migration
   phasing pulled from this report's service-map + risk register.
3. Keep the `unified-cloud-interface` (UCI) abstraction discipline — every new service that lands between now and Q3
   should not bake in GCP-specific calls outside UCI helpers. The Q3 migration then operates at one layer (UCI per-cloud
   impls) rather than spreading through every service.

---

## Open questions for operator

1. **Custody requirement**: does Copper or CEFFU have any explicit cloud-vendor preference or regulatory-residency
   requirement that would force AWS parity for May-23? If yes, this report's recommendation flips; if no (assumed), the
   recommendation stands.
2. **Storage actuals**: estimate is 11–22 TB. Is there a more authoritative number from the GCP billing console or a
   recent `gcloud storage du -s` run from a same-region GCE worker? Material for the egress one-time line item.
3. **Reserved-instance commitment appetite**: are you willing to commit to 1- or 3-year RIs/Savings Plans on AWS or CUDs
   on GCP? Could close the +5%–+7% list-pricing gap or create a bigger one. Affects the long-term TCO.
4. **Firebase auth scope**: confirm Firebase tier (auth + Firestore + Storage + Hosting) stays on GCP indefinitely. If
   yes, it removes the most expensive line item from any AWS migration. If no, add 4–6 engineer-weeks and ~$30k loaded.
5. **BigQuery analytics dependency**: how mission-critical is BQ specifically (vs `Athena`)? If any downstream BI
   dashboard or ML pipeline depends on BQ-specific features (geospatial, ML inline, table snapshots), call them out so
   the Q3 plan can choose Athena vs Redshift correctly.
6. **AWS account state**: is there an existing AWS account in `ap-northeast-1` with VPC + IAM foundation, or does the
   migration also include greenfield account/VPC/IAM setup? Adds 1–2 engineer-weeks if greenfield.
7. **Audit trail**: master plan `12ce828a` flagged "no cost-analysis report exists" as a blocker. Is THIS report the
   artifact that satisfies the gate, or does the gate require a vendor quote / solutions-architect review on the AWS
   side?

---

## Calculation appendix (for verification)

### Compute hours

- 5 always-on services × 24 × 30 = 3,600 hr
- 25 backfill VMs × 12 × 30 × 0.6 utilisation = 5,400 hr (peak rate; off-peak weeks lower)
- Plus burst spikes (per-asset-group rollouts) +1,000–3,000 hr/mo
- Total ~12,600 hr/mo midpoint

### Compute pricing (asia-northeast1 / ap-northeast-1, 2026-Q1 list)

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

### Storage pricing (2026-Q1 list)

- GCS Standard asia-northeast1: $0.026/GB/mo
- S3 Standard ap-northeast-1: $0.024/GB/mo
- 16 TB midpoint × 1024 = 16,384 GB
- GCS: $426/mo; S3: $393/mo

### Egress one-time

- GCS internet egress to AWS: $0.09/GB tier 1 (first 1 TB/mo can be lower)
- 16 TB ≈ 16,384 GB × $0.09 = $1,475
- Storage Transfer Service may discount; assume worst case for budget

---

## References

- Workspace docs: CLAUDE.md (VM Naming Convention, manifest concurrency principle, batch=live),
  `/codex/04-architecture/cloud-agnostic-migration.md` (canonical SSOT),
  `/codex/05-infrastructure/deployment-clusters-live-vs-batch.md`,
  `/codex/02-data/availability-manifest-and-data-status.md`.
- Master plan: `plans/active/master_to_live_defi_2026_05_23.plan.md` work-stream-D.
- Audit anchor: commit `12ce828a` master plan audit.
- Successor plan stub (proposed): `plans/ai/aws_migration_q3_2026.plan.md`.
- Pricing sources (verify before commitment): GCP pricing pages 2026-01 snapshot, AWS pricing pages 2026-01 snapshot,
  internal billing console.
