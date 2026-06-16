---
scope: [engineer, admin]
last_reviewed: 2026-05-29
---

# GCP Pub/Sub Topic Inventory

> **Executed**: 2026-05-26 by slot-7 (vm-cross-cutting) **Plan item**: `infrastructure_master` P2 — GCP Pub/Sub topic
> inventory + UCI MessageBus gap

## Summary

GCP project `central-element-323112` has **61 topics** (23 Terraform-managed event-bus + 38 legacy/unmanaged +
eventarc).

**AWS SNS gap decision**: AWS SNS mirroring is **NOT required** before post-cutover backfill VMs launch. Rationale: AWS
backfill VMs write to S3 only (manifest parquets + data). They do not consume or produce to the event bus. The event bus
feeds GCP-resident services (strategy-service, execution-service, alerting-service) which run on Cloud Run. AWS-side
equivalent becomes necessary only when services themselves migrate to AWS ECS — a post-cutover,
post-GCP-backfill-complete gate.

## Terraform-managed event-bus topics (23)

| Topic                             | Purpose                               |
| --------------------------------- | ------------------------------------- |
| `cascade-predictions`             | ML prediction cascades                |
| `circuit-breaker-events`          | Risk circuit breaker triggers         |
| `derivative-tickers`              | Derivative ticker data                |
| `eod-settlement`                  | End-of-day settlement signals         |
| `execution-results`               | Order execution outcomes              |
| `feature-updates`                 | Feature computation ready signals     |
| `features-cross-instrument-ready` | Cross-instrument feature readiness    |
| `features-delta-one-ready`        | Delta-one feature readiness           |
| `features-mtf-ready`              | Multi-timeframe feature readiness     |
| `fill-events`                     | Unified fill events (all venues)      |
| `health-alerts`                   | Service health alerts                 |
| `liquidations`                    | Liquidation events                    |
| `margin-warnings`                 | Margin warning events                 |
| `market-ticks`                    | Market tick data                      |
| `ml-predictions`                  | ML model predictions                  |
| `order-book-updates`              | Order book update events              |
| `order-requests`                  | Order submission requests             |
| `position-updates`                | Position update events                |
| `positions`                       | Position state                        |
| `risk-alerts`                     | Risk alert events                     |
| `service-lifecycle-events`        | Service STARTED/STOPPED/FAILED events |
| `sports-odds-ready`               | Sports odds data readiness            |
| `strategy-signals`                | Strategy trading signals              |

## Legacy/unmanaged topics (38)

These are **not** Terraform-managed and lack `purpose: event-bus` labels. Cleanup candidates — verify no active
consumers before deleting.

**Venue-specific fill-events (pre-consolidated):**

- `fill-events-AAVEV3-ETHEREUM`, `fill-events-HYPERLIQUID` (uppercase), `fill-events-UNISWAPV3-ETHEREUM`
- `fill-events-binance`, `fill-events-bybit`, `fill-events-deribit`, `fill-events-hyperliquid` (lowercase!),
  `fill-events-kalshi`, `fill-events-okx`, `fill-events-polymarket`
- **WARNING**: `fill-events-hyperliquid` and `fill-events-HYPERLIQUID` are duplicate case variants of the same venue.

**Service processing events (unmanaged):**

- `feature-processing-events`, `instruments-data-ready`, `instruments-processing-events`, `instruments-service-events`
- `market-data-processing-events`, `deployment-api-events`, `deployment-events`

**Operational/monitoring (unmanaged):**

- `deployment-alerts`, `deployment-status`, `system-health-events`, `alert-notifications`
- `alerting-service-events`, `audit-log-events`, `billing-alerts`, `risk-breach-alerts`
- `secret-rotation-alerts`, `defi-risk-events`

**Strategy/signal (unmanaged):**

- `strategy-signal-events`, `strategy-sports-signals`, `prediction-market-updates`
- `cascade-predictions` (note: this one IS managed, duplicate entry in legacy was a false positive), `lifecycle-events`

**Legacy infrastructure (likely stale):**

- `test`, `manager-tick`, `gen-inst-defs-job-trigger`, `orderbook_topic`, `orderbook_topicc` (typo!)
- `candle-bigquery-uploads`, `config-updates`

## UCI MessageBus abstraction gap

The deployment-service is **GCP Pub/Sub only**. No AWS SNS equivalent is wired. The `emit()` call in UTL's event bus
(`unified_trading_library.events.setup_events`) hardcodes GCP Pub/Sub via `pubsub_v1.PublisherClient`.

**Gap**: When services eventually run on AWS ECS, they cannot emit events without a `MessageBus` abstraction that routes
to SNS vs Pub/Sub based on `CLOUD_PROVIDER`.

**Implementation path** (when needed):

1. Create `MessageBus` interface in UTL with `emit(topic, message)` abstraction
2. GCP backend: `pubsub_v1.PublisherClient` (existing)
3. AWS backend: `boto3.client('sns')` — publish to SNS topic ARN from a topic-name→ARN registry
4. Route based on `UnifiedCloudConfig.cloud_provider`
5. Deploy-service Terraform: add SNS topic + subscription mirroring the 23 canonical event-bus topics

**Priority**: P2 post-cutover. Not blocking current work. AWS backfill VMs don't use event bus.

## Cleanup opportunities

1. **Duplicate case variants**: `fill-events-hyperliquid` + `fill-events-HYPERLIQUID` — delete one (check consumers).
2. **Typo topic**: `orderbook_topicc` — delete if unused.
3. **Legacy venue fill-events**: 10 venue-specific fill-events topics predate unified `fill-events`. Verify no consumers
   before deleting (these existed before the unified fill-events migration).
4. All 38 unmanaged topics should either be imported into Terraform or deleted after consumer audit.

## Subscriptions snapshot (30 active)

All subscriptions have 60s ack deadline except the Firebase eventarc subscription (600s). All Terraform-managed topics
have corresponding `-sub` subscriptions. Legacy topics mostly lack subscriptions (orphaned topics).

Full subscription list: see `gcloud pubsub subscriptions list --project=central-element-323112` output (2026-05-26).
