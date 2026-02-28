---
name: Topology Sharding Dimensions
overview: Add sharding dimensions, event trigger taxonomy, recovery/replay patterns, operational resilience (kill switches, circuit breakers, timestamp ordering, error retry policies, T+1 reconciliation), and comprehensive data flow annotations to the runtime topology SSOT (YAML, decisions doc, SVG).
todos:
  - id: yaml-v6-sharding
    content: Add sharding_dimensions per service, event_triggers taxonomy, recovery_patterns, pubsub_topic_templates to runtime-topology.yaml (v6)
    status: completed
  - id: decisions-doc-sections
    content: "Add sections 11-20 to RUNTIME_TOPOLOGY_DECISIONS.md: Sharding, Event Triggers, Recovery/Replay, Scaling Model, Underlying/Pool, Kill Switches, Error Retry Policy, Timestamp Ordering, T+1 Reconciliation, Persistence-to-Live Switchover"
    status: completed
  - id: svg-rebuild-comprehensive
    content: Rebuild RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg with dimension annotations, read arrows, recovery panel, topic structure panel, scaling reference, kill switch / circuit breaker flows, error retry policy reference
    status: completed
  - id: sharding-configs-update
    content: Update sharding.*.yaml configs with missing dimensions (instrument_type, feature_category, client, subaccount, strategy_id)
    status: completed
  - id: plan-update-refs
    content: Update consolidated_remaining_work.plan.md with topology-driven todos and SSOT references
    status: completed
isProject: false
---

# Topology: Sharding Dimensions, Event Triggers, Recovery Patterns

## Design Context

The topology needs three new layers of information:

1. **Sharding dimensions** — what defines one instance/job at the finest granularity
2. **Event trigger taxonomy** — what causes each service to process (stream, timer, event, schedule)
3. **Recovery/replay patterns** — how each service recovers from downtime, especially external data

These determine resource estimation, validation boundaries, horizontal/vertical scaling, and what infrastructure deployment-engine must provision.

---

## Key Architectural Decisions (from user)

### Two-Plane Model

- **Shared data plane (L1-L4):** Dimensions are `category x venue x instrument_type x ...`. No client concept. All clients see the same market data, features, and models.
- **Client-specific plane (L5-L6):** Adds `client x subaccount x strategy`. The "client" dimension enters at strategy-service.

### Batch Trigger Is Not a Dimension

- Batch is "run affirmatively" — the processing interval (day/week/month) comes from the sharding config in `unified-trading-deployment-v3/configs/sharding.*.yaml`. Not a trigger type.

### Finest Granularity = Scaling Unit

- The finest dimension is what gets published to a message bus topic. If you want one thing, that's one instance. If you want many, group into one VM with multiple threads. This gives clear horizontal/vertical scaling boundaries.

### Strategy NOT Sharded by Venue

- A strategy may span multiple venues (arb, spread). Shard by `strategy_id x client`. Has `underlying` concept for cross-instrument exposure aggregation. Pools = groups of correlated underlyings for portfolio-level risk.

### Position Is Raw, Aggregation Is Downstream

- PBM outputs at finest granularity (`client x subaccount x venue x instrument`). Risk, PnL, and reporting aggregate to higher dimensions (client x strategy, client x underlying, etc.).

### Three Execution Modes

- **Single-leg:** Standard order
- **Spread/multi-leg:** Legs tied by underlying, strategy manages working the legs
- **Atomic:** Blockchain DeFi atomic transactions, one instruction

### MDPS Holds Rolling Historical Window

- MDPS maintains a configurable rolling window of historical candles (~1 year) in memory/cache for downstream features warmup. Smallest timeframe drives the update trigger; larger timeframes update only on their natural boundaries.

### Features Triggered by MDPS Event

- Features services subscribe to MDPS completion events, not independent timers. This ensures features never run before MDPS has finished its aggregation cycle.

---

## Sharding Dimensions Per Service

### L1 — Data Ingestion

**instruments-service**

- Batch: `category x venue x date`
- Live: `venue` (poll ~15min, publish PubSub events for adds/removes/status)
- Current config: [sharding.instruments-service.yaml](unified-trading-deployment-v3/configs/sharding.instruments-service.yaml) already has `category, venue, date`

**market-tick-data-handler**

- Batch: `category x venue x instrument_type x data_type x date` (user added `instrument_type` — memory/SSD gets heavy per venue, splitting by instrument_type helps)
- Live: `venue x instrument_type x data_type` (one WebSocket per stream, multiplexed internally per venue)
- Current config: `category, venue, date` — needs `instrument_type, data_type` added
- Topics: `raw-ticks-{venue}-{instrument_type}-{data_type}` (finest granularity)

### L2 — Market Data Processing

**market-data-processing-service**

- Batch: `category x venue x instrument_type x date x timeframe`
- Live: `venue x instrument_type` (time-throttled, trigger = smallest timeframe ~15s)
- **New:** Holds rolling historical candle window (~1 year configurable) for downstream warmup
- **New:** Larger timeframes update on natural boundaries (1min every 4 triggers, 5min every 20, etc.)
- Current config: `category, venue, date` — needs `instrument_type, timeframe` added
- Topics: `processed-candles-{venue}-{instrument_type}-{timeframe}`

### L3 — Features

**features-delta-one-service, features-volatility-service**

- Batch: `category x venue x feature_category x date`
- Live: `venue x feature_category` (event-driven, triggered by MDPS completion event)
- **New dimension:** `feature_category` — allows swapping features in/out for optionality
- Current config: `category, feature_group, date` — `feature_group` is close to `feature_category`
- Topics: `features-{feature_category}-{venue}`

**features-calendar-service, features-onchain-service**

- Batch only: `category x date` (calendar), `protocol x chain x date` (onchain)

### L4 — ML Pipeline

**ml-training-service**

- Batch only: `model x instrument x timeframe x target_type x config` (scheduled ~quarterly)
- Current config: already has `instrument, timeframe, target_type`

**ml-inference-service**

- Batch: `model x venue x instrument x date`
- Live: `model x venue x instrument` (event-driven on features arrival)
- Current config: `instrument, timeframe, target_type, date`
- Topics: `predictions-{model}-{venue}-{instrument}`

### L5 — Strategy and Execution

**strategy-service**

- Batch: `strategy_id x client x date`
- Live: `strategy_id x client` (event-driven on predictions/market data)
- NOT sharded by venue — strategy may span venues (arb needs cross-venue view)
- Has `underlying` concept for aggregating exposure across instruments
- Has `pool` concept = groups of correlated underlyings for portfolio risk
- Current config: `category, config, date` — needs `strategy_id, client` added
- Topics: `trade-signals-{strategy_id}-{client}`

**execution-service**

- Batch: `client x subaccount x date` (uses default subaccount for backtest to keep uniform)
- Live: `client x subaccount` (one API key = one execution context)
- Category (CeFi/DeFi) determines routing, not a shard dimension
- Three modes: single-leg, spread/multi-leg, atomic (blockchain)
- Margin type (isolated/cross/unified) is metadata, not a shard dimension
- Instrument type determines routing protocol (options vs futures vs spot from api-contracts)
- Current config: `config, date` — needs `client, subaccount` added
- Topics: `order-events-{client}-{subaccount}-{venue}` (finest)

### L6 — Risk, PnL, Monitoring

**position-balance-monitor-service**

- Raw finest granularity: `client x subaccount x venue x instrument`
- Live: `client x venue` (event-driven on fills + periodic exchange reconciliation)
- Batch: `client x venue x date`
- Topics: `position-updates-{client}-{venue}` (aggregated per venue for downstream)

**risk-and-exposure-service**

- Subscribes to positions + market data, aggregates by `client x underlying x risk_category`
- Output dimensions: `client x strategy` (not finest raw position granularity)
- Live: event-driven on position/market data updates
- Has `pool` dimension for correlated underlying groups
- Topics: `risk-metrics-{client}`

**pnl-attribution-service**

- Subscribes to execution + risk + positions, aggregates
- Output dimensions: `client x strategy x date`
- Live: event-driven on execution/risk events
- Topics: `pnl-updates-{client}`

**alerting-service**

- Singleton (no sharding) for now
- Open question: what happens when alerting goes down? Options: (a) health-check watchdog on deployment-engine, (b) secondary standby instance, (c) Cloud Run auto-restart with PubSub replay

---

## Event Trigger Taxonomy


| Type                  | Cadence             | Services                                          | What Triggers It                        |
| --------------------- | ------------------- | ------------------------------------------------- | --------------------------------------- |
| continuous-stream     | ~0ms                | MTDH                                              | WebSocket message arrival               |
| time-throttled-short  | ~15s (smallest TF)  | MDPS                                              | Timer (aggregates buffer)               |
| event-driven-chain    | after MDPS          | features-delta-one, features-vol                  | MDPS completion PubSub event            |
| event-driven          | on upstream data    | ML inference, strategy, execution, PBM, risk, PnL | Upstream PubSub event                   |
| time-throttled-medium | ~15 min             | instruments                                       | Timer (poll venues)                     |
| scheduled-long        | ~quarterly          | ML training                                       | Cloud Scheduler / manual                |
| batch-affirmative     | per sharding config | all services in batch mode                        | Deployment command (not a trigger type) |


Multi-timeframe update rule for MDPS: smallest timeframe (e.g., 15s) drives the trigger. Larger timeframes update on natural boundaries:

- 1min = every 4 triggers
- 5min = every 20 triggers
- 15min = every 60 triggers
- 1h = every 240 triggers

---

## Recovery and Replay Patterns

### External Data Recovery (hardest)

**market-tick-data-handler recovery:**

- WebSocket drop: UMI `WebSocketFeedManager` reconnects with exponential backoff (max 10 attempts, 1s-32s)
- Gap detection: `GapInfo` model exists, `--mode check-gaps` CLI
- Recovery sources (venue-dependent):
  - Venue replay API (if supported — check api-contracts per venue)
  - Tardis live data replay stream (secondary data source)
  - GCS historical data (if persisted before crash)
- Recovery strategy: replay from last known good timestamp, fill gaps, then switch to live

**execution-service recovery:**

- Exchange position/order state: query exchange API for current state
- PBM reconciles independently from exchange feed
- Lost orders: exchange API query + PBM reconciliation detects discrepancies

**instruments-service recovery:**

- Instrument universe is slow-moving; simple re-fetch from venues on restart

### Internal Data Recovery (straightforward)

For services that process upstream data (MDPS, features, ML inference, strategy, risk, PnL):

- **Replay pattern:** Re-process from GCS persistence (the upstream service already persisted)
- **Catch-up math:** If processing 24h of data takes 2h, recovery takes 2h then you're caught up
- **Deployment question:** Same service instance on a separate thread (simpler), NOT a separate deployment. Replay thread processes historical while main thread processes live. Merge point when replay catches up.

### Persistence-to-Live Switchover

When a service starts or recovers, it needs to transition from reading historical (GCS) to consuming live (PubSub):

1. Service starts
2. Subscribes to live PubSub topic (messages queue while processing history)
3. Replays from GCS up to last persisted timestamp
4. Drains queued PubSub messages from step 2
5. At merge point: live processing takes over, historical replay thread stops
6. Any overlap is deduplicated by timestamp

This is the **concurrent replay + live with flip** pattern. Since we **publish + persist in parallel** (not write-then-publish), there may be a small overlap window where PubSub messages arrive before GCS persistence confirms. Consumers deduplicate by timestamp. The tradeoff: live latency is not blocked by persistence, but switchover needs timestamp-based dedup.

### MDPS Rolling Window Warmup

MDPS handles warmup for downstream:

- On startup: loads ~1 year of historical candles from GCS into rolling memory buffer
- Live: continuously updates buffer with new candles from MTDH stream
- Downstream features services read from MDPS (either GCS in batch, PubSub in live) and don't need their own warmup logic — MDPS provides candles with sufficient history context

---

## Operational Resilience

### Kill Switches and Circuit Breakers

**Current state:**

- execution-service has a kill switch (in-memory `threading.Event`, Secret Manager API key, REST endpoints `/kill-switch/activate|deactivate|status`)
- alerting-service has circuit breaker rules in `default_rules.yaml` (monitors `circuit_breaker_state == 2 = OPEN`)
- Circuit breaker command publishing from alerting to services: documented in architecture, NOT implemented

**Target design — two mechanisms:**

**Manual kill switch (human-initiated):**

- deployment-api exposes `/kill-switch/{service}/activate` endpoint (OAuth-gated)
- Propagates to target service via PubSub command topic `kill-switch-commands`
- Services that MUST honor kill switch: execution-service, strategy-service
- Kill switch state persisted (not just in-memory) — survives restarts
- live-health-monitor-ui shows kill switch status per service

**Automated circuit breaker (alerting-initiated):**

- alerting-service publishes `CIRCUIT_BREAKER_OPEN` events to `circuit-breaker-commands` PubSub topic
- Triggered by: risk breach thresholds, order rejection spike, balance discrepancy, connectivity loss
- Services subscribe and must honor: execution-service (halt orders), strategy-service (halt signal generation)
- Auto-reset: `CIRCUIT_BREAKER_CLOSE` after configurable cooldown OR manual reset via deployment-api
- Escalation chain: PubSub command -> Slack alert -> PagerDuty (if not acknowledged in N minutes)

### Timestamp Ordering and Late Messages

**Current state:** MTDH has timestamp validation (warnings only). UMI orderbook has `sequence_number` for gap detection. No enforcement.

**Target design:**

**Target design — publish as-is, consumer decides:**

- **No reorder buffer at the publisher.** MTDH publishes messages as they arrive from the exchange WebSocket. Each message carries BOTH:
  - `exchange_timestamp` — canonical ordering key (when the exchange says it happened)
  - `local_timestamp` — when our system received it (for latency monitoring)
- **Consumer responsibility:** Each downstream consumer decides whether to:
  - Process in arrival order (lowest latency, acceptable for most use cases)
  - Reorder by exchange_timestamp (correctness-critical consumers like PBM reconciliation)
  - Skip late messages (e.g., MDPS candle aggregation can ignore ticks that arrive after the candle closed)
- **Gap detection:** MTDH tracks sequence numbers per stream. Gaps trigger recovery from venue REST API or Tardis/Databento replay.
- **Why not enforce at publisher:** Enforcing ordering adds latency. Different consumers have different ordering requirements. Let the publisher be fast, let consumers be correct.

### Error Categorization and Retry Policy

**Current state:** `unified-internal-contracts` has `ErrorCategory` enum (RATE_LIMIT, TIMEOUT, NETWORK, SERVER_ERROR, VALIDATION, etc.) and `ErrorRecoveryStrategy` enum (RETRY, RETRY_WITH_BACKOFF, FALLBACK, FAIL_FAST, SKIP, ALERT). UTS has `is_retryable_error()`. `@with_retry` decorator planned but not implemented.

**Target design — retry before fail:**


| Error Category | Recovery Strategy  | Max Retries | Backoff                     | After Exhaustion                 |
| -------------- | ------------------ | ----------- | --------------------------- | -------------------------------- |
| RATE_LIMIT     | RETRY_WITH_BACKOFF | 5           | exponential 1s-60s + jitter | ALERT + SKIP (resume later)      |
| TIMEOUT        | RETRY              | 3           | linear 2s                   | ALERT + FAIL                     |
| NETWORK        | RETRY_WITH_BACKOFF | 10          | exponential 1s-120s         | CIRCUIT_BREAKER + ALERT          |
| SERVER_ERROR   | RETRY              | 3           | linear 5s                   | ALERT + FAIL                     |
| VALIDATION     | FAIL_FAST          | 0           | none                        | ALERT + LOG (data quality issue) |
| AUTH_FAILURE   | FAIL_FAST          | 0           | none                        | CIRCUIT_BREAKER + ALERT          |
| UNKNOWN        | RETRY              | 1           | 5s                          | ALERT + FAIL                     |


Key principle: **NETWORK errors get the most retries** (transient by nature). **VALIDATION and AUTH never retry** (they won't succeed on retry). **RATE_LIMIT skips and resumes** (don't burn through limits faster).

### T+1 Backtest vs Live Reconciliation (Two-Layer)

**Current state:** `strategy-validation-service` exists as empty skeleton. No implementation.

**Target design -- two separate T+1 reconciliations, aggregated:**

**Strategy T+1** (lives in `strategy-validation-service`):

- Validates: signals, strategy instructions, positions at snapshot points
- Compares: live signals vs batch-replayed signals given same inputs
- Output: strategy PnL = PnL assuming fills at benchmark price set by strategy instruction
- Dimensions: `strategy_id x client x date`
- ML signals should be identical (deterministic). Strategy instructions should be close (time-triggered).

**Execution T+1** (lives in `execution-service` or `strategy-validation-service`):

- Validates: order execution timing, fill quality, slippage
- Compares: live fills vs benchmark (TWAP/VWAP/arrival price)
- Output: execution alpha PnL = difference between actual fill price and benchmark
- Dimensions: `client x subaccount x venue x date`

**Aggregated PnL:**

- Overall PnL = strategy PnL (benchmark fills) + execution alpha PnL (actual vs benchmark)
- This decomposition answers: did we lose money because the strategy was wrong, or because execution was slow/expensive?
- Both run as separate batch jobs, then aggregate
- Full report output (no threshold initially -- eventually AI-interpreted)

### Order State Reconciliation on Connectivity Loss

**Current state:** execution-service has `reconcile_with_nautilus()` for internal OMS sync. WebSocket reconnection with exponential backoff in UMI.

**Target design:**

- On WebSocket reconnect: execution-service queries exchange REST API for all open orders and recent fills
- Compares exchange state vs internal OMS state
- Discrepancies: (a) missing fills -> apply to OMS, (b) unknown orders -> cancel or adopt, (c) stale orders -> cancel
- PBM independently reconciles positions from exchange feed vs accumulated fills
- Reconciliation events published to alerting-service for visibility

### Initial State Bootstrap

How each service gets its initial state on startup:


| Service             | Initial State Source                                | Method                                                         |
| ------------------- | --------------------------------------------------- | -------------------------------------------------------------- |
| instruments-service | Venue REST APIs                                     | Full fetch on start                                            |
| MTDH                | Venue WebSocket + Tardis replay                     | Subscribe + backfill gaps from GCS/Tardis                      |
| MDPS                | GCS historical candles                              | Load rolling window from GCS                                   |
| features-*          | GCS historical features                             | Load from GCS, recalculate if stale                            |
| ML inference        | GCS models + GCS/PubSub features                    | Load model from GCS, subscribe to feature PubSub               |
| strategy            | PBM positions + ML predictions + market data        | Subscribe to PBM (gets initial snapshot), ML, MDPS PubSub      |
| execution           | Exchange REST API (open orders) + Redis (hot state) | Query exchange, restore Redis state                            |
| PBM                 | Exchange REST API (positions + balances)            | Query exchange for current state, publish initial snapshot     |
| risk                | PBM positions + MDPS market data                    | Subscribe to PBM + MDPS PubSub                                 |
| PnL                 | GCS historical + live events                        | Load from GCS, subscribe to execution + risk PubSub            |
| alerting            | PubSub replay (if messages retained)                | Cloud Run auto-restart, PubSub retention replays missed events |


---

## Diagram Updates

The SVG needs these additions. Given complexity, use abbreviated labels and a reference panel.

### Per-service box annotations

Each service box gets 3 lines added:

- **Dims:** `cat x venue x inst_type x date` (batch) / `venue x inst_type` (live)
- **Trigger:** `stream` / `~15s` / `MDPS event` / `on signal` / `~15min` / `~quarterly`
- **Topics:** `raw-ticks-{v}-{it}-{dt}` (abbreviated topic template)

### Read flows (currently missing from SVG)

Add arrows showing what each service READS (blue dashed incoming), not just what it writes/publishes. Key reads:

- MDPS reads: raw ticks (MTDH), instruments (IS)
- Features read: candles (MDPS), instruments (IS)
- ML inference reads: features (features svcs), models (ML training GCS)
- Strategy reads: predictions (ML inference), market data (MDPS), positions (PBM)
- Execution reads: signals (strategy), market feed (MTDH)
- Risk reads: positions (PBM), market data (MDPS)
- PnL reads: execution results, risk metrics, positions

### Recovery panel

Add a "Recovery Patterns" panel to the SVG showing:

- External recovery: MTDH (venue replay / Tardis), execution (exchange API query)
- Internal recovery: replay from GCS persistence, catch-up on separate thread
- Switchover: concurrent replay + live with flip at merge point

### Topic structure panel

Add a "PubSub Topic Structure" reference showing topic naming convention:

- `{data-type}-{venue}-{instrument_type}-{...}` for shared data plane
- `{data-type}-{client}-{subaccount}-{venue}` for client-specific plane

### Scaling reference

Add a "Scaling Units" panel showing:

- Shared plane: scales by venue count x instrument type count
- Client plane: scales by client count x subaccount count
- One topic = one horizontal scaling unit

### Kill switch / circuit breaker flows

Add to the SVG:

- Red dashed arrows from deployment-api -> execution/strategy for manual kill switch
- Red dashed arrows from alerting -> execution/strategy for automated circuit breaker
- Kill switch REST endpoint annotation on deployment-api
- Circuit breaker state annotation on alerting-service

### Error retry policy reference panel

Add a "Retry Policy" reference panel showing the error category -> retry count -> backoff -> escalation table (abbreviated).

### Recovery / replay flow panel

Add a "Recovery Patterns" panel showing:

- External: MTDH reconnect (UMI backoff) -> gap detect -> venue replay / Tardis -> merge with live
- Internal: subscribe PubSub -> replay from GCS -> drain queue -> flip to live
- Execution: reconnect -> query exchange REST -> reconcile OMS -> resume
- Annotate: "write-then-publish guarantee: persist GCS BEFORE publishing PubSub"

### Timestamp annotation

Add annotation on MTDH box: "publishes as-is, tracks exchange_timestamp + local_timestamp + sequence_number"
Add annotation: "consumer decides: process in order / reorder by exchange_ts / skip late"

### Recovery source priority chain

Add compact reference showing MTDH recovery priority:

1. UMI WebSocket reconnect (brief disconnects, exponential backoff 1s-32s)
2. Venue REST API backfill (gaps < 3 months for most venues)
3. Tardis.dev / Databento replay (gaps > 3 months, as-if-live WS format)
4. GCS historical data (last resort, our own persistence)

### Venue replay capabilities reference

Add compact table: Tardis.dev 7yr WS replay crypto | Databento 7yr live-identical TradFi | Exchanges 3mo REST no replay | IBKR 6mo tick rate-limited

### Publish + persist annotation

Add to the transport bus panel: "publish + persist in PARALLEL. Consumer deduplicates by timestamp. Persistence does NOT block live publishing."

---

## SSOT Placement Map

Each piece of topology/resilience information lives where its content is governed. The `RUNTIME_TOPOLOGY_DECISIONS.md` doc serves as the aggregation layer -- references but does not duplicate.


| Topic                                              | SSOT Location                                                   | Governed By                        | Notes                                                                              |
| -------------------------------------------------- | --------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------- |
| Error categories, retry policies                   | `unified-internal-contracts` `schemas/errors.py`                | API/protocol schema                | Same errors regardless of deployment. ErrorCategory + ErrorRecoveryStrategy enums. |
| External API schemas, venue capabilities           | `api-contracts` (per-venue)                                     | External provider APIs             | Venue-specific: data types, rate limits, lookback, replay support.                 |
| Venue replay capabilities table                    | `api-contracts` (new section)                                   | External providers                 | Define there, reference from topology doc (DRY).                                   |
| Sharding dimensions                                | `runtime-topology.yaml`                                         | Deployment topology                | What dims define a shard = deployment/scaling decision.                            |
| Event triggers                                     | `runtime-topology.yaml`                                         | Deployment topology                | How/when services trigger = runtime behavior.                                      |
| Co-location, transport modes                       | `runtime-topology.yaml`                                         | Deployment topology                | Already lives here.                                                                |
| Messaging protocols (PubSub, in_memory, Redis)     | `runtime-topology.yaml` `message_bus` section                   | Deployment topology                | Already lives here. Which protocol for which flow.                                 |
| Storage patterns, data sinks (GCS, BQ, Redis)      | `runtime-topology.yaml` `storage_systems` + `persistence_flows` | Deployment topology                | Already lives here. What persists where.                                           |
| Kill switch topology (which services, propagation) | `runtime-topology.yaml`                                         | Deployment topology                | Which services have kill switches, how they propagate.                             |
| Kill switch implementation (API endpoints)         | `execution-service` (service-owned)                            | Service domain                     | Service owns its own kill switch API.                                              |
| Circuit breaker alert rules                        | `alerting-service` config (`default_rules.yaml`)                 | Operational thresholds             | Service-owned alerting config.                                                     |
| Timestamp ordering strategy                        | `runtime-topology.yaml`                                         | Runtime behavior policy            | Publisher publishes as-is; consumer policy documented here.                        |
| Recovery priority chains (per category)            | `runtime-topology.yaml`                                         | Deployment + data source selection | CeFi/TradFi/DeFi recovery chains.                                                  |
| Recovery architectural patterns                    | `RUNTIME_TOPOLOGY_DECISIONS.md`                                 | Architectural decisions            | Concurrent replay + live with flip, publish + persist in parallel.                 |
| Strategy T+1 reconciliation                        | `strategy-validation-service`                                   | Service domain                     | Strategy signal + instruction validation.                                          |
| Execution T+1 reconciliation                       | `execution-service` or `strategy-validation-service`           | Service domain                     | Order execution alpha PnL.                                                         |
| Reference data recovery                            | Trivial -- not a major SSOT concern                             | N/A                                | Latest live state; can drop a packet. No replay needed.                            |
| T+1 aggregation (strategy + execution PnL)         | `strategy-validation-service`                                   | Service domain                     | Orchestrates both T+1 results.                                                     |


**Codex SSOT index update:** The rationale for this placement (what governs = where it lives) should be documented in `unified-trading-codex/00-SSOT-INDEX.md` as the decision-making framework for SSOT placement. New entries needed for runtime-topology.yaml, venue replay capabilities in api-contracts, and the two-layer T+1 reconciliation.

---

## Files to Update

1. **[runtime-topology.yaml](unified-trading-deployment-v3/configs/runtime-topology.yaml)** — Add `sharding_dimensions`, `event_triggers`, `recovery_patterns`, `venue_replay_capabilities`, `kill_switches`, `error_retry_policy`, `pubsub_topic_templates`, `t_plus_1_reconciliation` sections (bump to v6)
2. **[RUNTIME_TOPOLOGY_DECISIONS.md](unified-trading-codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md)** — Add sections 11-20: Sharding Dimensions, Event Triggers, Recovery/Replay, Venue Replay Capabilities, Scaling Model, Underlying/Pool, Kill Switches and Circuit Breakers, Error Retry Policy, Timestamp Ordering, T+1 Reconciliation, Persistence-to-Live Switchover, Initial State Bootstrap
3. **[RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg](unified-trading-codex/04-architecture/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg)** — Full rebuild with: dimension annotations per service, read+write arrows, recovery panel, topic structure panel, scaling reference, kill switch / circuit breaker flows, retry policy reference, venue replay capabilities, timestamp strategy
4. **[consolidated_remaining_work.plan.md](unified-trading-pm/plans/cursor-plans/consolidated_remaining_work.plan.md)** — Update Agent Bootstrap SSOT references, add topology-driven todos for library support and deployment provisioning
5. **Sharding config files** in `unified-trading-deployment-v3/configs/sharding.*.yaml` — Add missing dimensions (`instrument_type`, `feature_category`, `client`, `subaccount`, `strategy_id`)
6. **[00-SSOT-INDEX.md](unified-trading-codex/00-SSOT-INDEX.md)** — Add SSOT placement rationale framework ("what governs it = where it lives"), add entries for runtime-topology.yaml, venue replay capabilities in api-contracts, two-layer T+1 reconciliation
7. **api-contracts** — Add venue replay capabilities table (Tardis, Databento, per-exchange lookback/replay support), referenced from topology doc (DRY)

---

## Resolved Design Decisions

1. **MDPS 1-year rolling window:** **Redis/memcached** — shared, survives restarts. Not in-memory.
2. **Publish + persist in parallel (NOT write-then-publish):** Persistence is too slow to block live publishing. Publish to PubSub immediately, persist to GCS in parallel. This means switchover may have a small overlap window — deduplicate by timestamp at the consumer level.
3. **Kill switch persistence:** **Secret Manager** — only a few ms latency, survives restarts, already implemented in execution-service.
4. **Circuit breaker auto-reset:** **Error-type-dependent**, determined by internal contracts schema:
  - Position mismatch → reconciliation on restart, then auto-reset
  - Network connectivity → restart execution stack, strategy services wait before sending more instructions, auto-reset when reconnected
  - Risk breach → manual reset only (human decision)
  - Rate limit → auto-reset after cooldown (per venue rate limit window)
5. **Timestamp ordering:** **No reorder buffer at publisher** — publish as messages arrive. Consumer decides whether to skip or reorder. Track BOTH local timestamp AND exchange timestamp so downstream can apply actions by either depending on use case.
6. **T+1 recon:** **Full report, no threshold initially.** Will eventually get an AI bot to interpret. Tracks:
  - ML signals: should be **identical** (deterministic models, same inputs)
  - Strategy instructions: should be **close** (time-triggered, assuming fill in period)
  - Fills/trades: will vary (matching engine differences, slippage)
  - Positions: should match at strategy instruction interval (both should be filled on previous instruction)
  - PnL: will vary with execution PnL (slippage, timing)
7. **Service downtime recovery depends on WHICH service AND protocol:**
  - MTDH down → everything downstream stalls. Recovery = venue replay or Tardis/Databento replay
  - MDPS down → features stall. Recovery = replay from MTDH GCS (fast, internal)
  - Execution down → strategy waits. Recovery = query exchange REST for order state, PBM reconciles positions
  - Alerting down → how do you get alerted that alerting is down? → deployment-engine health watchdog + Cloud Run auto-restart + PubSub retention replays missed events

---

## Venue Recovery Capabilities (from research)

**True replay providers (as-if-live WebSocket replay):**


| Provider       | Lookback | Replay Method                                                             | Asset Classes                       | Coverage                                               |
| -------------- | -------- | ------------------------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------ |
| **Tardis.dev** | ~7 years | WS-style replay (Tardis Machine) — identical format to live exchange feed | Crypto (40+ exchanges)              | Binance, OKX, Deribit, Bybit, Coinbase, dYdX, +35 more |
| **Databento**  | 7 years  | REST + live-identical replay client                                       | TradFi (equities, futures, options) | CME, Nasdaq, NYSE, Cboe, IEX, OPRA (60+ venues)        |


**Exchange native REST API lookback (no replay mode):**


| Exchange            | Trade Lookback                            | Orderbook     | Funding Rates | Method                          |
| ------------------- | ----------------------------------------- | ------------- | ------------- | ------------------------------- |
| **Binance spot**    | unlimited (paginate with fromId)          | snapshot only | N/A           | REST pagination                 |
| **Binance futures** | **3 months**                              | snapshot only | available     | REST pagination                 |
| **OKX**             | **3 months**                              | snapshot only | available     | REST pagination                 |
| **Deribit**         | shallow (public), indefinite (own trades) | snapshot only | available     | REST only                       |
| **Bybit**           | 2 years (7-day query windows)             | snapshot only | available     | REST pagination, intensive      |
| **IBKR**            | **6 months** (tick), ~2yr (1min bars)     | L1 only       | N/A           | TWS API callbacks, rate-limited |


**Key takeaway for MTDH recovery strategy by asset class:**

- **CeFi crypto:** Tardis.dev is the canonical recovery source. Covers all target venues with full L2 orderbook + trades + funding since 2019. WS-style replay means same code path as live.
- **TradFi:** Databento is the recovery source. Covers CME, Nasdaq, NYSE with L3 MBO data. Same code path as live.
- **DeFi:** The blockchain IS the source of truth. Always recoverable from any block number — query the chain (via The Graph, Alchemy, or direct RPC) for any historical state. No data loss possible as long as the chain is accessible. Recovery = replay from block N. This makes DeFi the simplest and most reliable recovery story of all asset classes.
- **IBKR:** Limited (6 month tick, aggressive rate limits). For deep recovery, may need alternative TradFi data source.
- **CeFi exchange native APIs are NOT sufficient for recovery** beyond 3 months for most venues. Always use Tardis/Databento as secondary recovery source.

**Recovery priority chain for MTDH (by category):**

CeFi crypto:

1. Venue WebSocket reconnect (UMI exponential backoff, handles brief disconnects)
2. Venue REST API backfill (for gaps < 3 months on most venues)
3. Tardis.dev replay (for longer gaps or full recovery, as-if-live WS format)
4. GCS historical data (last resort, our own persistence)

TradFi:

1. Venue reconnect
2. Databento replay (7yr lookback, live-identical format)
3. IBKR TWS API backfill (6mo tick, rate-limited)
4. GCS historical data

DeFi:

1. Chain RPC reconnect (The Graph / Alchemy / direct node)
2. Replay from block number (blockchain is immutable, full history always available)
3. No third-party dependency needed — the chain itself is the canonical source
