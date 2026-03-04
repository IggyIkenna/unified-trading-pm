> **Note:** Active task tracking has moved to `consolidated_remaining_work.plan.md`. This document retains historical
> context and completed-milestone records.

# Roadmap: Live Production (45.7% → 90.0%)

**Current State:** 45.7% live readiness
**Target:** 90.0% live readiness
**Gap:** 44.3 percentage points
**Last Updated:** 2026-02-11

---

## Executive Summary

This roadmap outlines the path from current 45.7% live readiness to 90% production-ready state for real-time trading.
Live production requires all batch production work (see `roadmap-batch-85pct.md`) PLUS live-specific infrastructure,
monitoring, and operational procedures.

**Prerequisite:** Complete batch roadmap to 85% before starting live-specific work.

**Key Differences from Batch:**

- Real-time WebSocket data ingestion (vs historical data replay)
- Per-client deployments with credential isolation
- Position reconciliation runs continuously (vs EOD batch)
- Alerting and incident response procedures
- Disaster recovery and rollback procedures
- 7-8 separate live deployments with package embedding

Program note:

- This roadmap is the live audit-remediation lane and runs alongside new capability requests in the same PM system.
- Status lifecycle for all work remains: `pending -> in_progress -> ready_for_testing -> uat_accepted -> done`.
- Owner defaults are bootstrapped by policy and can be overridden per work item.

Dual-cloud note:

- Live milestone completion requires dual-cloud readiness gates to be synchronized in codex docs, deployment checklist
  YAMLs, and GitHub PM fields.

---

## Phase 1: P0 Critical (Live-Blocking) — Weeks 1-4

**Objective:** Eliminate critical blockers specific to live trading. Assumes batch P0 items (SEC-05, COD-20) already
resolved.

**Estimated Completion:** 4 weeks
**Risk Level:** CRITICAL (these block live trading)

### 1.1 Client Credential Isolation (DOM-04, SEC-06)

**Priority:** P0
**Status:** PLANNED
**Effort:** 48 hours

**Description:**
No architecture exists for isolating client credentials. All services use a single service account. For live trading,
each client must have isolated credentials to prevent cross-client access and meet regulatory requirements.

**Affected Services:**

- execution-service (per-client deployments)
- strategy-service (reads client-specific parameters)
- All services (must not leak client data)

**Work Items:**

1. **Design credential isolation architecture** (12 hours)
   - Define per-client GCP service accounts
   - Design Secret Manager structure: `/clients/{client_id}/credentials/{venue}`
   - Define IAM policies: each client SA can only access own secrets/data
   - Design per-client GCS bucket structure: `gs://client-{client_id}-positions/`
   - Document in `07-security/client-credentials.md`

2. **Implement credential management service** (16 hours)
   - Create `client-credential-service/` in `unified-trading-services`
   - Build credential provisioning API (admin only)
   - Build credential retrieval API (validates client SA identity)
   - Implement credential rotation workflow
   - Add audit logging for all credential access

3. **Update execution-service** (12 hours)
   - Refactor to accept `--client-id` CLI flag
   - Load credentials from Secret Manager using client SA
   - Validate client SA identity matches `--client-id`
   - Update Dockerfile to accept client-specific service account
   - Update Cloud Run deployment to use per-client SAs

4. **Testing** (8 hours)
   - Unit tests: credential isolation logic
   - Integration tests: multi-client scenario (2 clients, verify no cross-access)
   - Security test: attempt cross-client access (should fail)
   - E2E test: deploy 2 client instances, verify isolated execution

**Acceptance Criteria:**

- [ ] Each client has dedicated GCP service account
- [ ] Credentials stored in Secret Manager with IAM isolation
- [ ] Execution-services accepts `--client-id` and loads client credentials
- [ ] Cross-client access blocked by IAM policies
- [ ] Audit logs track all credential access
- [ ] Documentation complete in `07-security/`

**Dependencies:**

- Requires GCP IAM admin permissions
- Requires batch credential cleanup (SEC-05) completed

---

### 1.2 Live Position Reconciliation (WRK-04)

**Priority:** P0
**Status:** PLANNED
**Effort:** 64 hours

**Description:**
Batch position reconciliation (WRK-03) runs EOD. Live trading requires continuous reconciliation (every 5 minutes) with
real-time alerting on breaks.

**Affected Services:**

- execution-service (position tracking)
- reconciliation-service (new continuous mode)
- alerting-service (new Slack/PagerDuty integration)

**Work Items:**

1. **Design live reconciliation architecture** (12 hours)
   - Define reconciliation frequency: every 5 minutes
   - Design multi-source reconciliation: internal position DB vs broker WebSocket position feeds vs trade confirmations
   - Define break severity levels: critical (>$10k discrepancy), warning (>$1k), info
   - Design notification workflow: critical → PagerDuty page, warning → Slack alert, info → log only
   - Document in `08-workflows/position-reconciliation.md` (update batch section)

2. **Implement continuous reconciliation engine** (24 hours)
   - Extend batch reconciliation service with `--mode live` flag
   - Implement sliding window reconciliation (last 5 minutes of trades)
   - Build real-time broker position feed consumers (per venue)
   - Implement break detection with severity classification
   - Add automatic position correction for small breaks (<$100)
   - Add manual intervention workflow for large breaks (halt trading, alert ops)

3. **Implement alerting service** (16 hours)
   - Create `alerting-service/` in `unified-trading-services`
   - Integrate Slack API for warning-level alerts
   - Integrate PagerDuty API for critical alerts
   - Add rate limiting (max 1 page per 15 minutes to avoid alert fatigue)
   - Add escalation policy: if not acknowledged in 5 minutes, page secondary oncall

4. **Testing** (12 hours)
   - Unit tests: reconciliation logic with synthetic breaks
   - Integration tests: mock broker position feeds with known discrepancies
   - E2E test: live mode with simulated trading, inject break, verify alert
   - Load test: verify reconciliation keeps up with 100 trades/second

**Acceptance Criteria:**

- [ ] Reconciliation runs every 5 minutes in live mode
- [ ] Breaks detected within 1 minute of occurrence
- [ ] Critical breaks trigger PagerDuty page (<30 seconds)
- [ ] Warning breaks trigger Slack alert
- [ ] Small breaks auto-corrected
- [ ] Large breaks halt trading and page oncall
- [ ] Documentation complete in `08-workflows/`

**Dependencies:**

- Requires batch reconciliation (WRK-03) completed
- Requires alerting infrastructure (OBS-14)

---

### 1.3 DATA_READY Event System (BATCH-04 Live Extension)

**Priority:** P0
**Status:** PLANNED
**Effort:** 32 hours

**Description:**
Batch services use DATA_READY events to coordinate pipeline execution. Live services need similar coordination but with
real-time streaming triggers instead of file-based triggers.

**Affected Services:**

- market-tick-data-service (publishes tick DATA_READY)
- market-data-processing-service (embedded, publishes bar DATA_READY)
- features-delta-one-service (subscribes to bar DATA_READY)
- strategy-service (subscribes to feature DATA_READY)
- execution-service (subscribes to signal DATA_READY)

**Work Items:**

1. **Design live event system** (8 hours)
   - Choose event bus: Pub/Sub vs in-process queues (for embedded packages)
   - Define event schema:
     `{event_type: "DATA_READY", dataset: "market-bars", timestamp: "2026-02-11T12:34:56Z", client_id: "client-123"}`
   - Design backpressure handling: what happens if downstream service can't keep up?
   - Document in `03-observability/domain-events.md`

2. **Implement event bus for embedded packages** (12 hours)
   - For single-process deployments (features → MDPS → MTHD), use in-process queues
   - Implement `EventBus` class in `unified-trading-services`
   - Add `publish_event()` and `subscribe_event()` methods
   - Implement backpressure: block publisher if queue full (configurable depth)

3. **Update live services** (8 hours)
   - market-tick-data-service: publish DATA_READY after each tick batch
   - market-data-processing-service: subscribe to tick DATA_READY, publish bar DATA_READY
   - features-delta-one-service: subscribe to bar DATA_READY, publish feature DATA_READY
   - strategy-service: subscribe to feature DATA_READY, publish signal DATA_READY

4. **Testing** (4 hours)
   - Integration test: full pipeline with event coordination
   - Test backpressure: slow consumer blocks producer correctly
   - Test end-to-end latency: tick → bar → feature → signal (<500ms)

**Acceptance Criteria:**

- [ ] All live services emit and consume DATA_READY events
- [ ] Events propagate through pipeline in <500ms
- [ ] Backpressure prevents memory overflow
- [ ] Logs show event latency metrics
- [ ] Documentation complete

**Dependencies:**

- Requires batch DATA_READY system (BATCH-04) completed

---

### 1.4 Disaster Recovery Procedures (WRK-01, WRK-02)

**Priority:** P0
**Status:** PLANNED
**Effort:** 40 hours

**Description:**
No disaster recovery procedures exist. For live trading, we need documented procedures for service failures, data
corruption, GCP outages, and erroneous trade scenarios.

**Affected Services:** ALL (live deployments)

**Work Items:**

1. **Document service failure recovery** (8 hours)
   - Define RTO (Recovery Time Objective): 5 minutes for critical services
   - Define RPO (Recovery Point Objective): zero data loss (all trades persisted)
   - Document restart procedures per service
   - Document position reconstruction from trade logs
   - Create runbook: `08-workflows/disaster-recovery.md`

2. **Implement automatic failover** (16 hours)
   - Configure Cloud Run auto-restart on failure
   - Implement health checks for each service
   - Configure multi-region deployment for critical services (execution-service)
   - Add service-level monitoring: alert if service down >1 minute

3. **Document erroneous trade procedures** (8 hours)
   - Define what constitutes an erroneous trade (e.g., fat finger, algorithm error)
   - Document trade cancellation workflow (per venue)
   - Document position unwinding procedures
   - Document client notification procedures
   - Create runbook: `08-workflows/incident-response.md`

4. **Conduct DR drill** (8 hours)
   - Simulate service failure: kill execution-service mid-trade
   - Verify automatic restart and position reconstruction
   - Simulate data corruption: inject bad data into GCS
   - Verify detection and recovery
   - Document lessons learned

**Acceptance Criteria:**

- [ ] Runbooks complete for all failure scenarios
- [ ] Automatic failover tested and working
- [ ] Multi-region deployment for critical services
- [ ] DR drill completed successfully
- [ ] RTO ≤5 minutes verified in drill

**Dependencies:**

- Requires alerting system (OBS-14)
- Requires position tracking (WRK-03/04)

---

### 1.5 Rollback Procedures (WRK-06)

**Priority:** P0
**Status:** PLANNED
**Effort:** 24 hours

**Description:**
No rollback procedures exist. For live trading, we need fast rollback capability if a deployment causes issues.

**Affected Services:** ALL (live deployments)

**Work Items:**

1. **Design rollback architecture** (6 hours)
   - Define rollback triggers: high error rate, position breaks, failed health checks
   - Define rollback mechanism: Cloud Run revision rollback vs blue-green deployment
   - Design rollback testing: verify old version still works before deploying new version
   - Document in `08-workflows/rollback.md`

2. **Implement automated rollback** (10 hours)
   - Configure Cloud Run revision retention: keep last 5 revisions
   - Create `rollback.sh` script per service
   - Implement automatic rollback on failed health checks (5xx errors >10% for 2 minutes)
   - Add manual rollback command: `./scripts/rollback.sh --revision previous`

3. **Testing** (8 hours)
   - Deploy intentionally broken version
   - Verify automatic rollback triggers
   - Test manual rollback script
   - Verify trading resumes after rollback

**Acceptance Criteria:**

- [ ] Rollback procedures documented
- [ ] Automatic rollback triggers on high error rate
- [ ] Manual rollback tested and working
- [ ] Rollback completes in <2 minutes

**Dependencies:**

- Requires health checks (WRK-01)

---

## Phase 1 Summary

| Work Item                            | Effort (hours) | Affected Services                 | Risk if Skipped                              |
| ------------------------------------ | -------------- | --------------------------------- | -------------------------------------------- |
| DOM-04/SEC-06: Client isolation      | 48             | execution-service, strategy       | Regulatory violation, cross-client leakage   |
| WRK-04: Live position reconciliation | 64             | execution-service, reconciliation | Undetected trading errors, P&L discrepancies |
| BATCH-04 live: DATA_READY events     | 32             | All live pipeline                 | Uncoordinated execution, stale data          |
| WRK-01/02: Disaster recovery         | 40             | ALL                               | Extended downtime on failure                 |
| WRK-06: Rollback procedures          | 24             | ALL                               | Cannot recover from bad deployments          |
| **Total**                            | **208 hours**  |                                   |                                              |

**Target Completion:** 4 weeks with 1.3 FTE (40 hours/week)

---

## Phase 2: P1 High Priority (Live Enhancements) — Weeks 5-10

**Objective:** Implement live modes for all pipeline services and enhance observability.

**Estimated Completion:** 6 weeks
**Risk Level:** MEDIUM

### 2.1 Live Mode for market-tick-data-service (LIVE-01)

**Priority:** P1
**Status:** PARTIAL (batch exists, live mode skeleton exists)
**Effort:** 48 hours

**Description:**
Market-tick-data-handler currently runs batch mode only. Need live mode to connect to exchange WebSockets and stream
tick data.

**Work Items:**

1. **Implement WebSocket adapters** (24 hours)
   - Binance WebSocket adapter (most important)
   - Coinbase WebSocket adapter
   - OKX WebSocket adapter
   - Implement reconnection logic (exponential backoff)
   - Implement selective venue initialization (only connect to needed venues)

2. **Implement live data sink** (12 hours)
   - Stream ticks to in-process queue (for embedded MDPS)
   - Also persist to GCS for audit trail (not on latency path)
   - Implement batching: write to GCS every 60 seconds or 10,000 ticks

3. **Testing** (12 hours)
   - Integration test: connect to testnet WebSockets
   - Test reconnection on simulated disconnect
   - Load test: verify keeps up with 1000 ticks/second
   - E2E test: live mode embedded in features-delta-one

**Acceptance Criteria:**

- [ ] Supports `--mode live` flag
- [ ] Connects to exchange WebSockets
- [ ] Streams ticks to in-process queue
- [ ] Persists to GCS for audit (not blocking latency path)
- [ ] Reconnects automatically on disconnect
- [ ] Tests pass

**Total Effort:** 48 hours

---

### 2.2 Live Mode for market-data-processing-service (LIVE-02)

**Priority:** P1
**Status:** PLANNED (batch exists, embedded package pattern designed)
**Effort:** 40 hours

**Description:**
Market-data-processing-service will not have standalone live deployment. It will be embedded as a package in feature
services. Need to ensure embedded mode works with live tick streams.

**Work Items:**

1. **Implement streaming aggregation** (20 hours)
   - Replace batch file reads with queue subscription (from MTHD)
   - Implement sliding window aggregation (1-second bars, 5-second bars, 1-minute bars)
   - Implement tumbling window emission (emit bar at end of period)
   - Handle late-arriving ticks (configurable window tolerance)

2. **Implement live data sink** (10 hours)
   - Publish bars to in-process queue (for downstream features)
   - Also persist to GCS for audit trail

3. **Testing** (10 hours)
   - Integration test: embedded in features-delta-one, feed synthetic ticks
   - Test sliding window logic (verify bar boundaries)
   - Test late tick handling
   - E2E test: full pipeline with live MTHD → MDPS → features

**Acceptance Criteria:**

- [ ] Embedded mode works with live tick streams
- [ ] Sliding window aggregation correct
- [ ] Bars published to queue in <50ms after window close
- [ ] Late ticks handled correctly (within tolerance)
- [ ] Tests pass

**Total Effort:** 40 hours

---

### 2.3 Live Mode for features-delta-one-service (LIVE-03)

**Priority:** P1
**Status:** PLANNED
**Effort:** 48 hours

**Description:**
Features-delta-one-service is highest priority for live trading (equity and crypto features). Must embed MDPS and MTHD
as packages and compute features in real-time.

**Work Items:**

1. **Implement package embedding** (16 hours)
   - Import market-tick-data-service as library (not subprocess)
   - Import market-data-processing-service as library
   - Wire in-process queues: MTHD → MDPS → features
   - Implement selective venue initialization (only needed venues)

2. **Implement streaming feature calculation** (20 hours)
   - Replace batch file reads with queue subscription (from MDPS)
   - Implement incremental feature calculation (update features on each new bar)
   - Implement feature state management (e.g., rolling windows, exponential moving averages)
   - Optimize for latency: <100ms from bar arrival to feature emission

3. **Testing** (12 hours)
   - Integration test: full embedded pipeline (MTHD → MDPS → features)
   - Test feature calculation correctness (compare to batch results)
   - Latency test: verify <100ms feature calculation
   - E2E test: live mode with simulated WebSocket ticks

**Acceptance Criteria:**

- [ ] Supports `--mode live` flag
- [ ] Embeds MDPS and MTHD as packages (single process)
- [ ] Computes features in <100ms per bar
- [ ] Feature values match batch results (on same input)
- [ ] Tests pass

**Total Effort:** 48 hours

---

### 2.4 Live Mode for features-volatility-service (LIVE-04)

**Priority:** P1
**Status:** PLANNED
**Effort:** 40 hours

**Description:**
Volatility features for options strategies. Lower priority than delta-one but still needed for volatility arbitrage.

**Work Items:** (Similar structure to features-delta-one)

1. Implement package embedding (12 hours)
2. Implement streaming volatility calculation (20 hours)
3. Testing (8 hours)

**Total Effort:** 40 hours

---

### 2.5 Live Mode for features-onchain-service (LIVE-05)

**Priority:** P1
**Status:** PLANNED
**Effort:** 40 hours

**Description:**
On-chain features for crypto strategies. Embeds MDPS and MTHD, adds on-chain data from The Graph.

**Work Items:** (Similar structure to features-delta-one)

1. Implement package embedding (12 hours)
2. Implement streaming on-chain feature calculation (20 hours)
3. Testing (8 hours)

**Total Effort:** 40 hours

---

### 2.6 Live Mode for ml-inference-service (LIVE-06)

**Priority:** P1
**Status:** PLANNED
**Effort:** 32 hours

**Description:**
ML inference for signal generation. Must load model once at startup, run inference on streaming features.

**Work Items:**

1. **Implement model loading** (8 hours)
   - Load LightGBM/XGBoost model from GCS at startup (not on each request)
   - Cache model in memory
   - Support hot model reload (on model update notification)

2. **Implement streaming inference** (16 hours)
   - Subscribe to feature queue (from features-delta-one)
   - Run inference on each feature vector
   - Publish predictions to signal queue
   - Optimize latency: <20ms inference time

3. **Testing** (8 hours)
   - Integration test: features → inference → signals
   - Test model hot reload
   - Latency test: verify <20ms inference
   - E2E test: full pipeline with live features

**Acceptance Criteria:**

- [ ] Supports `--mode live` flag
- [ ] Model loaded at startup (not per-request)
- [ ] Inference runs in <20ms
- [ ] Hot model reload works
- [ ] Tests pass

**Total Effort:** 32 hours

---

### 2.7 Live Mode for strategy-service (LIVE-07)

**Priority:** P1
**Status:** PLANNED
**Effort:** 48 hours

**Description:**
Strategy service is highest priority (generates trade signals). Must embed features-delta-one and ml-inference packages.

**Work Items:**

1. **Implement package embedding** (16 hours)
   - Import features-delta-one-service as library (which embeds MDPS and MTHD)
   - Import ml-inference-service as library
   - Wire in-process queues: features → inference → strategy
   - Implement client-specific parameter loading

2. **Implement signal generation** (20 hours)
   - Subscribe to prediction queue (from ml-inference)
   - Apply position sizing logic
   - Apply risk limits (max position, max drawdown)
   - Publish signals to execution-service

3. **Testing** (12 hours)
   - Integration test: full embedded pipeline (features → inference → strategy)
   - Test risk limits (verify position cap enforced)
   - Latency test: verify end-to-end <200ms (tick → signal)
   - E2E test: live mode with simulated ticks

**Acceptance Criteria:**

- [ ] Supports `--mode live` flag
- [ ] Embeds features and inference as packages
- [ ] Generates signals in <200ms end-to-end
- [ ] Risk limits enforced
- [ ] Tests pass

**Total Effort:** 48 hours

---

### 2.8 Alerting System (OBS-14)

**Priority:** P1
**Status:** PLANNED
**Effort:** 40 hours

**Description:**
No alerting system exists. For live trading, need Slack and PagerDuty integration for critical alerts.

**Work Items:**

1. **Design alerting architecture** (8 hours)
   - Define alert severity levels: critical (page oncall), warning (Slack), info (log only)
   - Define alert routing: service → alert manager → Slack/PagerDuty
   - Design alert aggregation (prevent alert fatigue)
   - Document in `03-observability/alerting.md`

2. **Implement alert manager** (16 hours)
   - Create `alert-manager/` service
   - Integrate Slack webhook API
   - Integrate PagerDuty Events API v2
   - Implement rate limiting (max 1 page per 15 minutes per service)
   - Implement alert deduplication (don't re-alert same issue)

3. **Add alerts to services** (12 hours)
   - Execution-services: alert on order rejection, position break
   - Strategy-service: alert on risk limit breach
   - Reconciliation-service: alert on position discrepancy
   - All services: alert on health check failure

4. **Testing** (4 hours)
   - Integration test: trigger alert, verify Slack message
   - Test rate limiting
   - Test PagerDuty escalation policy

**Acceptance Criteria:**

- [ ] Slack integration working
- [ ] PagerDuty integration working
- [ ] Alerts routed by severity
- [ ] Rate limiting prevents alert fatigue
- [ ] Documentation complete

**Total Effort:** 40 hours

---

### 2.9 Monitoring UI (OBS-15)

**Priority:** P1
**Status:** PLANNED
**Effort:** 60 hours

**Description:**
No real-time monitoring UI exists. For live trading, need dashboard showing positions, P&L, system health.

**Work Items:**

1. **Design monitoring UI** (12 hours)
   - Define dashboard views: system health, positions, P&L, trade log
   - Choose tech stack: Grafana vs custom React UI
   - Design data sources: BigQuery (historical) + Cloud Monitoring (real-time)
   - Document in `03-observability/README.md`

2. **Implement Grafana dashboards** (32 hours)
   - System health dashboard: CPU, memory, error rates per service
   - Trading dashboard: open positions, realized P&L, unrealized P&L
   - Trade log dashboard: recent trades, order status
   - Alert dashboard: recent alerts, oncall status

3. **Deploy monitoring infrastructure** (8 hours)
   - Deploy Grafana on Cloud Run or GKE
   - Configure data sources (BigQuery, Cloud Monitoring, Prometheus)
   - Set up authentication (Google OAuth)

4. **Testing** (8 hours)
   - Verify dashboards update in real-time
   - Test with simulated trading
   - User acceptance testing with traders

**Acceptance Criteria:**

- [ ] Grafana deployed and accessible
- [ ] Dashboards show real-time metrics
- [ ] Authentication working
- [ ] Traders can view positions and P&L

**Total Effort:** 60 hours

---

## Phase 2 Summary

| Work Item                         | Effort (hours) | Affected Services        | Benefit                       |
| --------------------------------- | -------------- | ------------------------ | ----------------------------- |
| LIVE-01: MTHD live mode           | 48             | market-tick-data-service | Real-time tick ingestion      |
| LIVE-02: MDPS live mode           | 40             | market-data-processing   | Real-time bar aggregation     |
| LIVE-03: Features delta-one live  | 48             | features-delta-one       | Real-time equity features     |
| LIVE-04: Features volatility live | 40             | features-volatility      | Real-time volatility features |
| LIVE-05: Features onchain live    | 40             | features-onchain         | Real-time on-chain features   |
| LIVE-06: ML inference live        | 32             | ml-inference             | Real-time signal generation   |
| LIVE-07: Strategy live            | 48             | strategy                 | Real-time trade signals       |
| OBS-14: Alerting                  | 40             | alert-manager            | Incident response             |
| OBS-15: Monitoring UI             | 60             | Grafana                  | Operational visibility        |
| **Total**                         | **396 hours**  |                          |                               |

**Target Completion:** 6 weeks with 1.7 FTE (40 hours/week)

---

## Phase 3: P2 Operational Excellence — Weeks 11-14

**Objective:** Improve operational readiness and performance.

**Estimated Completion:** 4 weeks
**Risk Level:** LOW (can defer to post-launch)

### 3.1 Performance Benchmarking (ANL-05)

**Priority:** P2
**Status:** PLANNED
**Effort:** 40 hours

**Description:**
No performance benchmarks exist. Need to establish latency and throughput baselines for live trading.

**Work Items:**

1. **Define performance SLOs** (8 hours)
   - Tick → signal latency: <200ms (P95), <500ms (P99)
   - Order placement latency: <100ms (P95)
   - Throughput: 1000 ticks/second sustained
   - Document in `04-architecture/performance-slos.md`

2. **Implement performance tests** (20 hours)
   - Create load testing framework (using Locust or custom)
   - Test tick ingestion throughput
   - Test end-to-end latency (tick → signal)
   - Test order placement latency

3. **Run benchmarks and analyze** (8 hours)
   - Run tests in staging environment
   - Identify bottlenecks
   - Optimize hot paths (if needed)

4. **Add performance monitoring** (4 hours)
   - Add latency metrics to Grafana
   - Add throughput metrics
   - Add alerts for SLO violations

**Acceptance Criteria:**

- [ ] SLOs documented
- [ ] Performance tests pass
- [ ] Latency metrics in Grafana
- [ ] Bottlenecks identified and documented

**Total Effort:** 40 hours

---

### 3.2 Multi-Region Deployment (INF-07)

**Priority:** P2
**Status:** PLANNED
**Effort:** 48 hours

**Description:**
All services currently deployed to single region (us-central1). For production-grade reliability, deploy critical
services to multiple regions with automatic failover.

**Work Items:**

1. **Design multi-region architecture** (8 hours)
   - Choose primary region: us-central1 (closest to Coinbase, Binance.US)
   - Choose secondary region: us-east1 (failover)
   - Define which services need multi-region: execution-service (yes), strategy (yes), features (no, can tolerate brief
     downtime)
   - Document in `04-architecture/scaling.md`

2. **Implement multi-region deployment** (24 hours)
   - Update Terraform to deploy critical services to both regions
   - Configure Cloud Load Balancer with health checks
   - Configure automatic failover (route to secondary if primary unhealthy)
   - Test failover: kill primary region, verify traffic routes to secondary

3. **Implement data replication** (12 hours)
   - Configure multi-region GCS buckets (dual-region)
   - Configure BigQuery multi-region dataset
   - Verify data consistency across regions

4. **Testing** (4 hours)
   - Simulate primary region failure
   - Verify failover completes in <2 minutes
   - Verify trading resumes in secondary region

**Acceptance Criteria:**

- [ ] Critical services deployed to 2 regions
- [ ] Automatic failover tested
- [ ] Data replicated across regions
- [ ] Failover completes in <2 minutes

**Total Effort:** 48 hours

---

### 3.3 Cost Optimization (ANL-06)

**Priority:** P2
**Status:** PLANNED
**Effort:** 32 hours

**Description:**
Live trading will incur higher costs (always-on services vs batch). Need to optimize costs before scaling to many
clients.

**Work Items:**

1. **Analyze current costs** (8 hours)
   - Review GCP billing for past 3 months
   - Break down by service: Cloud Run, GCS, BigQuery, networking
   - Identify top cost drivers

2. **Implement cost optimizations** (16 hours)
   - Right-size Cloud Run instances (reduce CPU/memory if over-provisioned)
   - Implement GCS lifecycle policies (delete ticks after 30 days, move to Coldline after 90 days)
   - Optimize BigQuery queries (partition pruning, avoid SELECT \*)
   - Implement data compression (use Parquet instead of CSV)

3. **Set up cost monitoring** (8 hours)
   - Create cost dashboard in Grafana (using BigQuery billing export)
   - Set up budget alerts (alert if monthly cost >$5k)
   - Document cost per client in `09-analysis/cost-analysis.md`

**Acceptance Criteria:**

- [ ] Cost analysis complete
- [ ] Optimizations implemented
- [ ] Monthly cost reduced by ≥20%
- [ ] Cost monitoring dashboard live

**Total Effort:** 32 hours

---

### 3.4 Compliance Audit Trail (WRK-05)

**Priority:** P2
**Status:** PLANNED
**Effort:** 24 hours

**Description:**
For regulatory compliance, need immutable audit trail of all trades, orders, and position changes.

**Work Items:**

1. **Design audit trail schema** (4 hours)
   - Define events to log: order placed, order filled, order canceled, position opened, position closed
   - Design schema: timestamp, event_type, client_id, venue, instrument, details
   - Choose storage: GCS (immutable) + BigQuery (queryable)
   - Document in `08-workflows/audit-trail.md`

2. **Implement audit logging** (12 hours)
   - Update execution-service to log all order events
   - Update strategy-service to log all signal generation events
   - Implement tamper-proof logging (cryptographic hashing)
   - Write to GCS with write-once policy

3. **Implement audit queries** (4 hours)
   - Create BigQuery views for common audit queries
   - Create CLI tool: `ucs-audit query --client-id X --start-date Y`

4. **Testing** (4 hours)
   - Verify all events logged
   - Verify immutability (cannot modify GCS objects)
   - Test audit queries

**Acceptance Criteria:**

- [ ] All order and position events logged
- [ ] Logs immutable (write-once GCS policy)
- [ ] Audit queries work correctly
- [ ] Documentation complete

**Total Effort:** 24 hours

---

## Phase 3 Summary

| Work Item                        | Effort (hours) | Affected Services   | Benefit                  |
| -------------------------------- | -------------- | ------------------- | ------------------------ |
| ANL-05: Performance benchmarking | 40             | All live services   | Latency optimization     |
| INF-07: Multi-region deployment  | 48             | Critical services   | High availability        |
| ANL-06: Cost optimization        | 32             | All services        | Reduce operational costs |
| WRK-05: Compliance audit trail   | 24             | execution, strategy | Regulatory compliance    |
| **Total**                        | **144 hours**  |                     |                          |

**Target Completion:** 4 weeks with 1 FTE (36 hours/week)

---

## Milestone: Live 90% Ready

**Total Effort:** 748 hours (Phase 1: 208h, Phase 2: 396h, Phase 3: 144h)

**Timeline:**

- **Prerequisites:** Batch 85% ready (10 weeks, see `roadmap-batch-85pct.md`)
- **Phase 1 (Weeks 11-14):** P0 live-specific blockers
- **Phase 2 (Weeks 15-20):** Live modes for all services
- **Phase 3 (Weeks 21-24):** Operational excellence

**Total Timeline:** 24 weeks from start (6 months with 1.5 FTE average)

**Success Metrics:**

- [ ] Live readiness ≥90% on audit re-run
- [ ] All P0 items resolved (client isolation, live reconciliation, disaster recovery, rollback)
- [ ] All P1 items resolved (live modes for 7 services, alerting, monitoring UI)
- [ ] ≥50% of P2 items resolved (performance benchmarking, multi-region, cost optimization)
- [ ] End-to-end latency <200ms (P95) from tick to signal
- [ ] Disaster recovery procedures tested
- [ ] First client live trading successfully

---

## Deployment Topology (7-8 Live Deployments)

Based on `04-architecture/deployment-topology-diagrams.md`:

1. **TARDIS persistence** -- market-tick-data-service streaming to GCS (not on latency path)
2. **instruments-service** -- standalone venue API calls
3. **features-calendar-service** -- standalone calendar data
4. **features-delta-one-service** -- embeds MDPS (embeds MTHD), connects to exchanges
5. **features-volatility-service** -- embeds MDPS (embeds MTHD), connects to exchanges
6. **features-onchain-service** -- embeds MDPS (embeds MTHD), connects to exchanges + The Graph
7. **strategy-service** -- embeds features-delta-one + ml-inference
8. **execution-service** -- per-client deployment, embeds MTHD package

**Key principles:**

- Each deployment is a separate Cloud Run service
- Package embedding is nested (features → MDPS → MTHD, all in-process)
- Each deployment connects to exchanges directly (no shared WebSocket service)
- Selective venue initialization (only connect to needed venues)

---

## Risk Assessment

| Risk                                    | Likelihood | Impact   | Mitigation                                                              |
| --------------------------------------- | ---------- | -------- | ----------------------------------------------------------------------- |
| Live mode latency >200ms                | Medium     | Critical | Performance benchmarking in Phase 3; optimize hot paths                 |
| WebSocket disconnect during trading     | High       | Critical | Implement robust reconnection logic with exponential backoff            |
| Position reconciliation false positives | Medium     | High     | Tune tolerance thresholds; require manual confirmation for large breaks |
| Multi-client credential leakage         | Low        | Critical | Security audit of IAM policies; pen testing                             |
| Disaster recovery drill fails           | Medium     | High     | Run multiple drills; iterate on runbooks                                |
| Cost spirals with many clients          | Medium     | Medium   | Implement per-client cost monitoring; shut off if budget exceeded       |

---

## Dependencies on Other Workstreams

- **Batch roadmap:** Must complete to 85% before starting live work (prerequisite)
- **unified-trading-services:** Needs EventBus, AlertManager, ClientCredentialService implementations
- **GCP IAM:** Need permissions for per-client service accounts, Secret Manager
- **Exchange testnet access:** Need for integration testing

---

## Success Criteria (Re-Audit Checklist)

After completing all phases, re-run audit to verify:

- [ ] All batch items from `roadmap-batch-85pct.md` passing
- [ ] DOM-04/SEC-06: PASS (client credential isolation)
- [ ] WRK-04: PASS (live position reconciliation)
- [ ] WRK-01/02: PASS (disaster recovery procedures)
- [ ] WRK-06: PASS (rollback procedures)
- [ ] LIVE-01..07: PASS (all services support live mode)
- [ ] OBS-14: PASS (alerting system)
- [ ] OBS-15: PASS (monitoring UI)
- [ ] ANL-05: PASS (performance benchmarking)
- [ ] Overall live readiness ≥90%

---

## Next Steps

1. **Immediate:** Complete batch roadmap to 85% (see `roadmap-batch-85pct.md`)
2. **Week 11:** Start Phase 1 live work (client isolation, live reconciliation)
3. **Week 15:** Start Phase 2 live modes (MTHD, MDPS, features)
4. **Week 21:** Start Phase 3 operational excellence
5. **Week 24:** Re-run audit, prepare for first client go-live

**Owner:** Engineering Lead
**Stakeholders:** All service owners, DevOps, Trading Operations, Compliance
