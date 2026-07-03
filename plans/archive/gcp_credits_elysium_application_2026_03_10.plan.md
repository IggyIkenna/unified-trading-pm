---
doc_type: plan
title: gcp-credits-elysium-application-2026-03-10
summary:
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
overview: Apply for $150k GCP credits via Google Cloud for Startups using Elysium Capital as the applicant entity, with materials covering the AI/ML DeFi trading use case and GCP spend estimate.
type: business
epic: epic-business
superseded_by: presentations_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: none, deployment: none, business: B6}
repo_gates:
- {repo: unified-trading-pm, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: application materials and business documentation — no infrastructure deployment required. BR N/A pending: business sign-off tracked at plan level (B6); repo gate records only artifact delivery status.'}
depends_on: [elysium-defi-lite-fork-2026-03-10, aws-migration]
isProject: false
---

# Plan: GCP Credits Application via Elysium Partnership

status: superseded superseded_by: presentations_2026_03_13 superseded_date: 2026-03-13

## Context

GCP credits ran out on 2026-02-09. Running the full system (60 repos, 100TB data, Cloud Run services) costs ~$3–5k/month
— not sustainable pre-revenue. Elysium Capital as a fintech client/partner enables an application to Google Cloud for
Startups (or similar program) on their behalf. Expected outcome: $100k–$200k in GCP credits covering 2–3 years. AWS $40k
credits provide bridge coverage while waiting.

---

## Phase 1: Program research

### P1.1 — Identify applicable programs

File: `unified-trading-pm/business/gcp-credits-elysium/program-research.md`

Research these programs (in priority order):

| Program                              | Credits     | Requirements             | Best fit                |
| ------------------------------------ | ----------- | ------------------------ | ----------------------- |
| Google Cloud for Startups            | Up to $200k | VC-backed or accelerator | Elysium as applicant    |
| Google for Startups Accelerator (AI) | Up to $200k | AI/ML focus, startup     | Strong fit — trading AI |
| Google Cloud Partner Credits         | Variable    | System integrator        | If we register as GSI   |
| Google Cloud Research Credits        | Up to $100k | Academic/research        | Less likely             |

**Most likely path**: Elysium applies as a DeFi fintech startup with AI/ML trading use case. We provide the technical
architecture, GCP services list, and expected spend estimate. Elysium provides company details, AUM, and investment
thesis.

### P1.2 — Eligibility checklist

- [ ] Elysium: registered company (confirm jurisdiction)
- [ ] Elysium: not already receiving GCP credits elsewhere
- [ ] Use case: AI/ML (trading algorithms) — qualifies for AI Accelerator program
- [ ] Revenue: pre-revenue or early-stage (confirm)
- [ ] Funding: check if VC-backed requirement applies

---

## Phase 2: Application materials

### P2.1 — GCP spend estimate

File: `unified-trading-pm/business/gcp-credits-elysium/gcp-spend-estimate.md`

**Monthly GCP spend at scale (production):**

| Service                                  | Monthly           | Notes                     |
| ---------------------------------------- | ----------------- | ------------------------- |
| Cloud Run (14 services, 1 instance each) | $400              | 0.25–1 vCPU per service   |
| GCS storage (100TB)                      | $2,000            | $0.02/GB standard storage |
| BigQuery (queries + storage)             | $500              | Depends on query volume   |
| Pub/Sub (events)                         | $200              | ~500M events/month        |
| Cloud Build CI                           | $100              | 60 repos × builds         |
| Artifact Registry                        | $50               | Docker images             |
| Secret Manager                           | $50               | ~100 secrets              |
| Cloud Logging + Monitoring               | $200              | 10GB logs/day             |
| Cloud Scheduler                          | $20               | ~50 jobs                  |
| Cloud SQL (Grafana)                      | $100              | db-g1-small               |
| **Total**                                | **~$3,620/month** |                           |

Annual: ~$43k/year → 3-year ask: ~$130k → request $150k (buffer)

### P2.2 — Technical architecture summary (1 page)

File: `unified-trading-pm/business/gcp-credits-elysium/technical-summary.md`

**AI/ML Systematic Trading Infrastructure on GCP**

- 60 microservices on Cloud Run (auto-scaling, serverless)
- 100TB+ financial data on GCS + BigQuery (crypto, DeFi, TradFi, Sports)
- Real-time event processing via Pub/Sub (500M+ events/month)
- ML models for signal generation (multi-asset, multi-strategy)
- Deployed in: us-central1 (primary), asia-northeast1 (low-latency to Asian exchanges)
- GCP services in use: Cloud Run, GCS, BigQuery, Pub/Sub, Secret Manager, Cloud Build, Artifact Registry, Cloud
  Scheduler, Cloud Logging, Cloud Monitoring

**Why GCP**: multi-region low-latency execution, BigQuery for financial analytics at scale, Pub/Sub for real-time data
pipelines, Vertex AI roadmap for model serving.

### P2.3 — Use case description

File: `unified-trading-pm/business/gcp-credits-elysium/use-case.md`

**Use Case: AI-Powered Systematic DeFi Trading**

Elysium Capital is a DeFi-focused systematic fund using machine learning to identify and capture yield opportunities
across 14 DeFi protocols. The system:

1. Ingests real-time data from blockchains (Ethereum, Arbitrum, Base, Polygon, Solana)
2. Computes features for ML signal generation (100+ features, updated every minute)
3. Runs ML inference to generate trading signals
4. Executes on-chain transactions via smart contract interactions

Infrastructure requirement: GCS for 100TB historical data storage, BigQuery for ML feature storage and backtesting
analytics, Cloud Run for microservice execution, Pub/Sub for real-time data pipelines.

### P2.4 — Elysium company profile

File: `unified-trading-pm/business/gcp-credits-elysium/elysium-profile.md`

Template — requires Elysium to fill in:

- [ ] Company legal name + jurisdiction
- [ ] Registration date
- [ ] AUM (or "pre-AUM, raising")
- [ ] Investment strategy overview
- [ ] Team (2–5 key people, backgrounds)
- [ ] Website (if any)
- [ ] Funding status (self-funded, angel, VC)

### P2.5 — Application draft

File: `unified-trading-pm/business/gcp-credits-elysium/application-draft.md`

Full application in Google Cloud for Startups format:

```
Company name: Elysium Capital [or legal entity name]
Website: [URL]
Description: DeFi systematic trading fund powered by ML
Stage: Early stage / seed
Vertical: FinTech / Crypto / AI+ML
GCP services needed: Cloud Run, GCS, BigQuery, Pub/Sub, Secret Manager
Current monthly GCP usage: $0 (new project)
Expected monthly spend at scale: $3,600
Credits requested: $150,000
Use of credits:
  - 60% Cloud Storage (100TB financial dataset)
  - 25% Cloud Run + Pub/Sub (real-time trading infrastructure)
  - 15% BigQuery + other services (ML + analytics)
How GCP enables our business:
  Multi-region Cloud Run for low-latency execution near exchange matching engines.
  BigQuery for backtesting analytics on 100TB of financial data.
  Pub/Sub for real-time signal propagation across 60 microservices.
```

---

## Phase 3: Submission and follow-up

### P3.1 — Elysium review

Share `application-draft.md` + `elysium-profile.md` with Elysium. Get their approval on all company-specific details and
use case description. Timeline: by March 24 (1 week before board meeting).

### P3.2 — Submit application

Submit before March 31. Preferred: Google Cloud for Startups at https://cloud.google.com/startups

### P3.3 — Follow-up cadence

Week 1: Confirm receipt with Google Week 2–4: Weekly check-in with assigned Google Cloud startup team If approved:
credits applied to Elysium's GCP project, shared with us

### P3.4 — Backup plan (bridge while waiting)

AWS $40k credits active → migrate dev/staging workloads:

- CI/CD: GitHub Actions → CodeBuild (already has buildspec.aws.yaml)
- Dev services: ECS Fargate (low priority, for testing)
- GCP prod project: minimal footprint (only what's needed for live trading)

---

## Verification Gates

- [ ] `program-research.md` complete with best-fit program identified
- [ ] `gcp-spend-estimate.md` with line-item monthly breakdown
- [ ] `application-draft.md` complete (all fields filled)
- [ ] Elysium has reviewed and approved company-specific sections
- [ ] Application submitted (confirmation email received)
- [ ] Backup AWS migration plan documented in `gcp-spend-estimate.md`

## Files Created

- `unified-trading-pm/business/gcp-credits-elysium/` (new directory)
  - `program-research.md`
  - `gcp-spend-estimate.md`
  - `technical-summary.md`
  - `use-case.md`
  - `elysium-profile.md`
  - `application-draft.md`

## Dependencies

- `elysium_defi_lite_fork_2026_03_10.md` (technical context for application)
- `aws_migration.md` (backup plan if GCP credits delayed)
