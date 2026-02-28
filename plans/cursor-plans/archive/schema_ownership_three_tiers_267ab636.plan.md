---
name: Schema Ownership Three Tiers
overview: "Full execution plan: contracts vs implementations split, MessagingScope (IN_PROCESS/SAME_VM/CROSS_VM), EventEnvelope/EventSinkSpec (no GCS in contracts), hot state vs append-only log, StateStore, BaseExecutionAdapter hierarchy, request-response-error symmetry, no empty try/except, Phase A-F checklist."
todos:
  - id: msg-redis-inmem
    content: Add MessagingScope (IN_PROCESS/SAME_VM/CROSS_VM) and Redis vs in-memory to UCS and codex
    status: completed
  - id: msg-aws
    content: Implement QueueEventSink AWS (SNS+SQS) in UCS
    status: completed
  - id: storage-fast
    content: Add StateStore interface (get/set/compare-and-set, scan_by_key_prefix) + rebuild-from-log
    status: completed
  - id: api-contracts-restructure
    content: "Restructure api-contracts: api_contracts_external/ + unified_normalised_contracts/"
    status: pending
  - id: unified-internal-repo
    content: Create unified-internal-contracts repo with full setup
    status: pending
  - id: utei-clob
    content: Add BaseExecutionAdapter; rename BaseOrderAdapter → BaseCLOBAdapter in UTEI
    status: completed
  - id: sports-adapter
    content: Create BaseSportsAdapter (Betfair reuses CLOB; Pinnacle uses Sports)
    status: completed
  - id: amm-adapter
    content: Add BaseAMMAdapter in UDEI (DeFi swaps, pools)
    status: completed
  - id: manifest-update
    content: Add unified-internal-contracts, unified-sports-execution-interface to workspace-manifest.json
    status: completed
  - id: vcr-ownership
    content: Document VCR SSOT and per-repo cassette ownership in codex
    status: completed
  - id: dep-enforcement
    content: "Add quality gate: api-contracts never imports unified-internal-contracts"
    status: completed
  - id: dep-enforcement-cloud-sdks
    content: "Add quality gate: unified-internal-contracts cannot import cloud SDKs"
    status: completed
isProject: false
---

# Schema Ownership, Cloud-Agnostic Sync, Execution Adapters — Full Execution Plan

## 0. Core Fix: Contracts vs Implementations

**Contracts repos** (pure types, no cloud libs):

- **api-contracts** — external raw schemas + canonical normalised schemas; NO cloud SDKs, NO service imports
- **unified-internal-contracts** — internal message envelopes, topic names, request/response/error schemas; NO cloud SDKs, NO implementations

**Implementation repos** (adapters/clients):

- **unified-cloud-interface** (or unified-events-interface) — actual Pub/Sub, SNS/SQS, Redis, GCS, S3, etc.
- Services and execution interfaces depend only on contracts + abstract interfaces; choose backends via config

**Rule:** Contracts never import implementations. This prevents circular dependencies.

---

## 1. Messaging: Redis vs In-Memory vs Cross-VM

### MessagingScope (Contract-Level)

`MessagingScope` enum in unified-internal-contracts — backend-agnostic:


| Scope          | Use when                                     |
| -------------- | -------------------------------------------- |
| **IN_PROCESS** | Single process; internal API calls           |
| **SAME_VM**    | Multi-process or multi-thread on one VM/host |
| **CROSS_VM**   | Network boundary; cross-host                 |


**Backends** (implementation-level, in unified-cloud-interface):

- In-memory queue → IN_PROCESS
- Redis → SAME_VM or CROSS_VM (if Memorystore/ElastiCache configured)
- Pub/Sub, SNS+SQS → CROSS_VM (durable fan-out)

**Rule of thumb:** Latency-critical + simple fanout → Redis. Durability + fanout + replayability → Pub/Sub or SNS+SQS. Single process → in-memory.

### Existing Redis Patterns (Reuse, Don't Rebuild)


| Location                                 | What exists                                                                          | Reuse                                                                                   |
| ---------------------------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| **unified-trading-deployment-v3**        | `api/utils/cache.py` — RedisCache, aioredis, TTL, in-memory fallback                 | Cache pattern; Redis publish in `deployment_events.py` for `deployment:updated` channel |
| **unified-trading-deployment-v3**        | `r.publish("deployment:updated", deployment_id)`                                     | Redis Pub/Sub pattern for cross-process notification                                    |
| **api-contracts/internal/pubsub.py**     | `InternalPubSubTopic` enum — fill-events-{venue}, order-requests, market-ticks, etc. | Move to unified-internal-contracts; canonical topic names                               |
| **unified-config-interface**             | `config-updates` topic for hot-reload                                                | Already uses Pub/Sub; add Redis channel equivalent                                      |
| **unified-cloud-interface** .cursorrules | Cache: Redis (Memorystore), Redis (ElastiCache)                                      | Documented; implementations in UTD v3                                                   |


**UCS had redis_cache.py — DELETED** (library_foundation plan). UTD v3 has its own cache. For messaging abstraction, add Redis backend to UCS/UEI using patterns from UTD v3, not rebuilding from scratch.

### When to Use Which


| MessagingScope         | Use when                                                | Backend                  | Need Redis? |
| ---------------------- | ------------------------------------------------------- | ------------------------ | ----------- |
| **IN_PROCESS**         | One thread; internal API calls, one strip of code       | In-memory queue          | No          |
| **SAME_VM**            | Multiple threads/processes need shared state on same VM | Redis Pub/Sub            | Yes         |
| **CROSS_VM** (Redis)   | Cross-VM; need lower latency than Pub/Sub               | Memorystore, ElastiCache | Yes         |
| **CROSS_VM** (Pub/Sub) | Cross-VM; durability, fan-out, standard choice          | GCP Pub/Sub, AWS SNS+SQS | No          |


**Rule:** Cross-VM Redis (Memorystore/ElastiCache) is faster than Pub/Sub. Use when latency matters. Pub/Sub for durability/fan-out. Config drives which backend; services use abstracted interfaces only.

**Where to put it:** unified-internal-contracts = canonical topic names, envelopes, message schemas. unified-cloud-interface = publishers/subscribers for Pub/Sub, SNS/SQS, Redis.

### Messaging Backends


| Type                          | GCP              | AWS              | Local (same-VM)  |
| ----------------------------- | ---------------- | ---------------- | ---------------- |
| **Cross-VM (Pub/Sub)**        | Google Pub/Sub   | SNS + SQS        | —                |
| **Cross-VM (Redis)**          | Memorystore      | ElastiCache      | —                |
| **Multi-thread (Redis)**      | Memorystore      | ElastiCache      | Redis            |
| **Single-thread (in-memory)** | In-process queue | In-process queue | In-process queue |


### Topic Names and Equivalents (unified-internal-contracts)

**Topic/channel names are internal contracts.** unified-internal-contracts owns:


| Concept             | GCP Pub/Sub                                                      | Redis channel         | AWS SNS                               |
| ------------------- | ---------------------------------------------------------------- | --------------------- | ------------------------------------- |
| **Logical topic**   | `projects/{project}/topics/fill-events-binance`                  | `fill-events-binance` | `arn:aws:sns:...:fill-events-binance` |
| **Canonical names** | InternalPubSubTopic enum (from api-contracts/internal/pubsub.py) | Same string           | Same topic name                       |


**Schema:** `unified_internal_contracts/messaging.py` (or `messaging_topics.py`):

- `MessagingScope` enum — IN_PROCESS, SAME_VM, CROSS_VM
- `MessagingTopic` enum — canonical topic/channel names (fill-events-{venue}, order-requests, market-ticks, etc.)
- `TopicBackend` — GCP | AWS | Redis
- Mapping: logical name → backend-specific resource path

**Setup:** Config/env for REDIS_URL, PUBSUB_PROJECT, SNS_TOPIC_ARN. Topic names come from unified-internal-contracts; backend selection from config.

**Cross-VM Redis deployment:** UTD v3 has `scripts/setup-redis.sh` for Memorystore (GCP). Add equivalent for ElastiCache (AWS). When REDIS_URL points to Memorystore/ElastiCache, Redis works cross-VM — faster than Pub/Sub. Optional; configure when latency matters.

---

## 2. Event Logging vs Cloud Sink (No GCS in Contracts)

**Correct abstraction split:**

**Contracts** (unified-internal-contracts):

- `EventEnvelope`, `EventType`, `EventSinkSpec` — backend-agnostic; no GCS/S3 in contract layer

**Interfaces** (unified-events-interface or unified-cloud-interface):

- `EventSink` — write events
- `EventReader` — read/replay events

**Implementations** (unified-trading-services, unified-cloud-interface):

- `GcsEventSink`, `S3EventSink`, `LocalFsEventSink`
- `BigQueryEventSink` only if required (usually not for hot path)

**Rule:** Rename "GCS event sync tier" to "Storage-backed EventSink implementation". GCSEventSink → StorageEventSink (or GcsEventSink as implementation); no cloud-specific types in contracts.

---

## 3. Storage Tiers: Hot State vs Append-Only Log

BigQuery and GCS are **not** for hot order state. Two distinct concerns:

### A) Hot State (fast reads/writes)


| Cloud     | Options                                                         |
| --------- | --------------------------------------------------------------- |
| **GCP**   | Redis (Memorystore), Cloud SQL / AlloyDB, Firestore (trade-off) |
| **AWS**   | Redis (ElastiCache), DynamoDB, Aurora/Postgres                  |
| **Local** | In-memory + SQLite/Postgres; or Redis + SQLite                  |


### B) Append-Only Immutable Log (idempotent replay, audit)


| Cloud     | Options                                                                                              |
| --------- | ---------------------------------------------------------------------------------------------------- |
| **GCP**   | Pub/Sub → GCS (files) and/or BigQuery for analytics; optionally Bigtable for low-latency time-series |
| **AWS**   | Kinesis (or MSK) → S3; optionally DynamoDB streams or Aurora logical log                             |
| **Local** | Append-only file (JSONL/Parquet) + SQLite WAL                                                        |


**Key design:** Hot store is derived from the append-only log. If hot store dies, rebuild from the log.

### StateStore Interface

Define in unified-cloud-interface or unified-trading-services:

- `StateStore` interface: `get`, `set`, `compare-and-set`, `scan_by_key_prefix`
- Backends: Redis, DynamoDB, CloudSQL/Aurora, SQLite
- Rebuild-from-log flow: event log → state rebuild

### OLAP and Object (unchanged)


| Tier       | Use case        | GCP      | AWS    | Local            |
| ---------- | --------------- | -------- | ------ | ---------------- |
| **OLAP**   | Batch analytics | BigQuery | Athena | SQLite/Parquet   |
| **Object** | Batch files     | GCS      | S3     | Local filesystem |


---

## 4. Execution Adapters: BaseExecutionAdapter Hierarchy

Use a domain adapter family approach (future-proof):


| Interface                | Owner       | Venues                                                                    |
| ------------------------ | ----------- | ------------------------------------------------------------------------- |
| **BaseExecutionAdapter** | UTEI/UDEI   | Very thin: lifecycle, ids, capability flags                               |
| **BaseCLOBAdapter**      | UTEI        | Order book venues: Binance, Coinbase, OKX, IBKR, Betfair (exchange-style) |
| **BaseAMMAdapter**       | UDEI        | DeFi swaps, pools: Uniswap, Curve                                         |
| **BaseSportsAdapter**    | New or UTEI | Sportsbooks, exchanges, scraping: Betfair (reuses CLOB), Pinnacle         |


Betfair implements BaseCLOBAdapter (exchange-like). Pinnacle implements BaseSportsAdapter. Maximises reuse without wrong abstraction.

---

## 5. Schema Repos: Request-Response-Error Symmetry

### Three Layers, Each With Request + Response + Errors


| Layer                            | Request                                | Response                        | Errors                                       | Purpose                                                |
| -------------------------------- | -------------------------------------- | ------------------------------- | -------------------------------------------- | ------------------------------------------------------ |
| **api_contracts_external**       | Raw request schemas (send to exchange) | Raw response schemas (get back) | Raw error schemas (venue-specific)           | External API shapes                                    |
| **unified_normalised_contracts** | Canonical request                      | Canonical response              | Canonical error (human-readable, grouped)    | One-hop normalisation; execution interfaces stay light |
| **unified_internal_contracts**   | Internal request (service-to-service)  | Internal response               | Internal error (pub-sub, db, table failures) | Service-to-service messaging                           |


### Why This Matters

- **Execution interfaces** (UMI, UTEI) focus on translation only. Handling logic is normalised regardless of venue.
- **Raw → normalised errors** in api-contracts. New errors get added to schemas; no ad-hoc handling.
- **Not all venues have all error types.** Normalise what you can into groups; human-readable where possible. Venue-specific exceptions exist but are explicit — no empty try/except.
- **Same for internal:** Every failure mode (pub-sub, db read/write, table) has a schema. Handle all; no empty try/except.
- **Config, events, data storage** — same methodology. Know exactly what failure looks like.

### api-contracts Layout (After Restructure)

```
api-contracts/
├── api_contracts_external/         # Raw: request, response, errors per venue
│   ├── binance/
│   │   ├── request.py              # BinanceOrderRequest, etc.
│   │   ├── response.py             # BinanceTradeResponse, BinanceOrderResponse
│   │   └── errors.py               # BinanceError, BinanceRateLimitError
│   ├── deribit/
│   └── ...
├── unified_normalised_contracts/   # Canonical: request, response, errors
│   ├── domain.py                   # CanonicalTrade, CanonicalOrderBook
│   ├── execution.py                # CanonicalOrder, CanonicalFill, CanonicalOrderRequest
│   ├── errors.py                   # CanonicalError, CanonicalRateLimitError (grouped)
│   └── ...
└── ...
```

### unified-internal-contracts Layout (New Repo)

```
unified-internal-contracts/
├── unified_internal_contracts/
│   ├── messaging.py              # MessagingTopic enum; topic names; GCP Pub/Sub, Redis channel, AWS SNS mapping
│   ├── ml.py                     # ML prediction request/response
│   ├── risk.py                   # Risk metrics, exposure
│   ├── features.py               # Feature vectors
│   ├── events.py                 # EventEnvelope, EventType, EventSinkSpec (contracts; no GCS/S3)
│   ├── pubsub.py                 # Typed message bodies (from api-contracts/internal/pubsub.py)
│   ├── requests.py               # Internal service request schemas
│   ├── responses.py              # Internal service response schemas
│   └── errors.py                 # Internal errors (pub-sub failure, db failure, etc.)
├── pyproject.toml
├── scripts/quality-gates.sh
├── scripts/quickmerge.sh
└── ...
```

**messaging.py** — Canonical topic/channel names; backend-agnostic. Same logical name maps to:

- GCP Pub/Sub: `projects/{project}/topics/{topic}`
- Redis: channel name `{topic}` (e.g. `fill-events-binance`, `deployment:updated`)
- AWS SNS: `arn:aws:sns:{region}:{account}:{topic}`

### Dependency Rules (No Cycles)

- api-contracts: stdlib + pydantic only; no unified-* imports
- unified-internal-contracts: imports api-contracts (normalised) only
- T2 libraries: import T0 only; never T1; never each other

### Schema Evolution and Versioning

Each layer versions independently. Bump when schemas change:


| Layer                            | Example                            | When to bump                                   |
| -------------------------------- | ---------------------------------- | ---------------------------------------------- |
| **api_contracts_external**       | v1.2.0 — Binance added field       | New venue, new field (minor), breaking (major) |
| **unified_normalised_contracts** | v2.0.0 — Breaking canonical format | Breaking change in CanonicalTrade, etc.        |
| **unified_internal_contracts**   | v1.5.0 — New event type            | New internal schema, new event type            |


Use semantic versioning. Consumers pin ranges (e.g. `>=1.0.0,<2.0.0`). Document in SCHEMA_VERSIONS.md.

**Versioning = known good state:** If passing quality gates, integration tests have run. Deploy same version as integration test → no surprises. Request-response versions track compatibility.

---

## 5b. No Empty Try/Except — Fail Explicitly

**Rule:** No empty `except:` or `except Exception: pass`. Every error path must be handled.


| Scope                                     | Requirement                                                                      |
| ----------------------------------------- | -------------------------------------------------------------------------------- |
| **External (api-contracts)**              | Raw errors → normalised errors. New errors added to schemas. No silent catch.    |
| **Internal (unified-internal-contracts)** | Every failure mode (pub-sub, db, table) has schema. Handle all.                  |
| **Quality gates**                         | Linter catches bad code organisation. Same methodology for config, events, data. |


---

## 5c. Error Handling Strategy (Per Error Type)

Not fallbacks that do nothing. Choose the right strategy per error:


| Strategy               | When                                  | Example                          |
| ---------------------- | ------------------------------------- | -------------------------------- |
| **Retry**              | Transient (rate limit, network blip)  | Retry with backoff               |
| **Fail fast**          | Invalid input, auth failure           | Raise immediately                |
| **Exit job/shard/day** | Bad data for one date                 | Skip that shard, continue others |
| **Exit whole process** | Fatal (config corrupt, unrecoverable) | Shutdown cleanly                 |
| **Circuit breaker**    | Upstream dependency failing           | Stop calling; propagate          |


**Goal:** High availability — keep going with errors in a safe way. Not: keep going on bad errors, or always fail and need human intervention for transient errors. Adapt strategies over time.

---

## 5d. Circuit Breakers and DAG Dependency Failure

- **Central logging** of config, data, events → DAG of dependencies
- **Circuit breakers** = handling certain errors (exchange connectivity, P&L moves, position reconciliation)
- **Propagate failure** when upstream issues can't be resolved by usual mechanisms
- Same pattern for exchange connectivity, P&L moves, position reconciliation — all use central config/events to fail dependencies

---

## 6. Testing SSOT and VCR Ownership

### Who Owns What


| Asset                                   | SSOT Owner                 | Location                                                   | Consumers                                                |
| --------------------------------------- | -------------------------- | ---------------------------------------------------------- | -------------------------------------------------------- |
| **VCR cassettes** (raw venue HTTP only) | api-contracts              | `api_contracts/<venue>/mocks/*.yaml`                       | UMI, UTEI, market-tick-data-handler, instruments-service |
| **Example JSON** (raw venue)            | api-contracts              | `api_contracts/<venue>/examples/*.json`                    | Schema validation, tests                                 |
| **Record script**                       | api-contracts              | `scripts/record_vcr_cassettes.py`                          | Run once with network; commit cassettes                  |
| **Replay tests**                        | api-contracts              | `tests/test_vcr_replay.py`                                 | CI (no live requests)                                    |
| **Interface VCR usage**                 | Per interface              | UMI, UTEI set `cassette_library_dir` to api-contracts path | No duplicate cassettes                                   |
| **Internal contract fixtures**          | unified-internal-contracts | `tests/fixtures/`                                          | Services consuming internal schemas                      |


**VCR scope:** Only for HTTP. WebSocket capture is separate (different tooling/flow).

### VCR Flow

1. **Record once** (with API keys): `uv run python scripts/record_vcr_cassettes.py [--venue binance]`
2. **Commit cassettes** to api-contracts
3. **Replay in CI** (no keys): `pytest tests/test_vcr_replay.py`
4. **Consumers** reference api-contracts mocks path; never duplicate

### Who Owns Testing


| Repo type                      | Unit tests                      | Integration tests       | VCR                                        |
| ------------------------------ | ------------------------------- | ----------------------- | ------------------------------------------ |
| **api-contracts**              | Owns schema validation, replay  | —                       | Owns record + replay                       |
| **unified-internal-contracts** | Owns internal schema validation | —                       | N/A (no external API)                      |
| **UMI, UTEI, UPI**             | Own raw→canonical conversion    | Own cross-interface     | Use api-contracts cassettes                |
| **Services**                   | Own business logic              | Own service integration | Use api-contracts if calling external APIs |


### Testing Strategy for Normalization (api-contracts)

Normalization lives in api-contracts; tests live there too:

```python
# api-contracts/tests/test_normalization.py
def test_binance_to_canonical():
    raw = BinanceTrade(...)
    canonical = normalize_trade(raw)
    assert isinstance(canonical, CanonicalTrade)

# Property-based testing for all venues
@given(venue=sampled_from(ALL_VENUES))
def test_normalization_preserves_core_fields(venue):
    # All venues must normalize to same core fields
```

- **Per-venue tests:** `test_binance_to_canonical`, `test_deribit_to_canonical`, etc.
- **Property-based:** `test_normalization_preserves_core_fields` — all venues produce same core CanonicalTrade fields.
- **Hypothesis:** Use `@given` with `sampled_from(ALL_VENUES)` for coverage.

### Circular Dependency Rules

- api-contracts: stdlib + pydantic only; no unified-* imports
- unified-internal-contracts: stdlib + pydantic + (optionally) unified_normalised_contracts; **no cloud SDKs** (google-cloud-*, boto3, redis clients)
- Implementations (unified-cloud-interface, services) can import both contracts repos
- Never the other direction

**CI guardrails (blocking):**

- Fail if api-contracts imports unified-*
- Fail if unified-internal-contracts imports cloud SDKs (google-cloud-*, boto3, redis clients)

---

## 7. Migration Phases and Execution Order

**Execution:** All phases in one day via parallel agents. Ordering matters — later phases depend on earlier.

### Phase 1 (First — api-contracts restructure)

**Duration:** ~2 weeks equivalent; parallel agents compress to hours.

- Create `api_contracts_external/` and `unified_normalised_contracts/` subpackages
- Move existing files; update imports
- **No breaking changes** — add re-exports so existing `from api_contracts.internal import X` still works during transition
- Add `tests/test_normalization.py` with per-venue and property-based tests
- **Docs:** Update api-contracts README, CONTRIBUTING
- **Cursor rules:** None yet (Phase 1 is internal restructure)
- **PM tracking:** Create `unified-trading-pm/plans/ai/SCHEMA_OWNERSHIP_MIGRATION.md` with Phase 1 checklist

### Phase 2 (After Phase 1 — extract unified-internal-contracts)

**Duration:** ~1 week equivalent.

- Create unified-internal-contracts repo with full setup
- Move `ml.py`, `risk.py`, `features.py`, `events.py`, `pubsub.py` from api-contracts
- Services update imports: `from unified_internal_contracts import X`
- Remove internal schemas from api-contracts (after consumer migration)
- **Docs:** unified-internal-contracts README, ARCHITECTURE; update api-contracts
- **Cursor rules:** Add rule for "import internal schemas from unified-internal-contracts"
- **PM tracking:** Update SCHEMA_OWNERSHIP_MIGRATION.md Phase 2 checklist

### Phase 3 (After Phase 2 — BasePosition pattern)

**Duration:** ~1 week equivalent.

- Add BasePosition, BaseOrder (if needed) to api-contracts `unified_normalised_contracts/`
- UMI, UTEI, UPI implement extensions (ExecutionPosition, MarketDataPosition, CanonicalPosition)
- **Docs:** codex schema-governance.md, extension pattern
- **Cursor rules:** Add rule for "extend base schemas from api-contracts; do not duplicate"
- **PM tracking:** Update SCHEMA_OWNERSHIP_MIGRATION.md Phase 3 checklist

### Phase A–F Drop-In Checklist (Alternative View)

Maps to tightened execution order; can replace or augment Phase 1–3:


| Phase | Focus                                  | Key tasks                                                                                                                                                                                                                |
| ----- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **A** | Contracts + dependency guards          | Create unified-internal-contracts scaffold; move InternalPubSubTopic → messaging_topics.py; add CI guardrails (contracts no cloud SDKs; api-contracts no unified-*)                                                      |
| **B** | api-contracts restructure              | Split api_contracts_external/, unified_normalised_contracts/; add canonical error taxonomy; normalization tests; VCR record + replay                                                                                     |
| **C** | Cloud-agnostic messaging + event sinks | Define EventEnvelope, EventSinkSpec, MessagingScope in internal contracts; implement PubSubPublisher/Sub, SnsSqsPublisher/Sub, RedisPublisher/Sub, InProcessQueue; implement GcsEventSink, S3EventSink, LocalFsEventSink |
| **D** | Order state storage                    | Define StateStore interface (get/set/compare-and-set, scan_by_key_prefix); implement Redis, DynamoDB, CloudSQL/Aurora, SQLite backends; define rebuild-from-log flow                                                     |
| **E** | Execution adapters                     | Rename BaseOrderAdapter → BaseCLOBAdapter; add BaseExecutionAdapter, BaseAMMAdapter, BaseSportsAdapter; update consumers; delete legacy                                                                                  |
| **F** | Codebase cleanup + "no ghosts"         | Remove old logic references; only allow legacy naming in migration/ or compat/ shims; enforce no empty try/except in ruff + CI                                                                                           |


### Parallel Agent Strategy

- **Phase 1:** 2–3 agents — one for api_contracts_external move, one for unified_normalised move, one for tests
- **Phase 2:** 2 agents — one for repo creation + file move, one for consumer updates
- **Phase 3:** 2 agents — one for base schemas, one for interface extensions

---

## 7b. Parallel Execution Blocks (5 Agents × 5 Sub-Agents)

**Goal:** Implement large parts in parallel. Blocks must be independent where possible; highlight when blocked.

### Block Dependency Graph

```
BLOCK A (Foundation) — MUST COMPLETE FIRST
├── A1: api-contracts restructure (external + normalised + errors)
├── A2: Add request/response/error schemas to api-contracts
└── A3: Add normalization tests + no-empty-except rule to quality gates

BLOCK B — BLOCKED BY A
├── B1: Create unified-internal-contracts repo + request/response/errors
├── B2: Extract internal schemas from api-contracts
└── B3: Add internal error schemas (pub-sub, db, table failures)

BLOCK C — BLOCKED BY A (can run parallel with B)
├── C1: UMI — use normalised request/response/errors; remove ad-hoc handling
├── C2: UTEI — use normalised request/response/errors; remove ad-hoc handling
└── C3: UDC, UPI — same pattern

BLOCK D — BLOCKED BY B
├── D1: Services importing internal — switch to unified-internal-contracts
├── D2: Remove empty try/except across all services
└── D3: Add error handling strategy (retry/fail-fast/exit-job) per error type

BLOCK E — BLOCKED BY B, C (can run parallel with D)
├── E1: UCS — StateStore, EventSink/EventReader impls (Gcs/S3/LocalFs); circuit breaker / DAG dependency failure
├── E2: Codex + cursor rules — error handling, no-empty-except, request-response-error
└── E3: Config, events, data storage — same methodology docs
```

### Independent vs Blocked


| Block | Independent? | Blocked by |
| ----- | ------------ | ---------- |
| **A** | Yes          | —          |
| **B** | No           | A          |
| **C** | No           | A          |
| **D** | No           | B          |
| **E** | No           | B, C       |


**Agent assignment:** 5 agents. Agent 1 does A; Agents 2–3 do B and C in parallel after A; Agents 4–5 do D and E after B/C. Each agent can spawn 5 sub-agents (Chord-style) for subtasks.

### Scope: Every Repo


| Repo type                     | Action                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------- |
| **All repos (current + new)** | Update to use centralised, normalised schemas and error handling                      |
| **Remove**                    | Non-compliant code — ad-hoc error handling, empty try/except, custom request/response |
| **Result**                    | Dramatically reduced service code; fewer errors; better maintainability               |


---

## 8. Critical Requirements: Documentation, Cursor Rules, PM Tracking

### Documentation Updates (Required)


| Repo                           | Doc                                           | Update                                                                                 |
| ------------------------------ | --------------------------------------------- | -------------------------------------------------------------------------------------- |
| **api-contracts**              | README, CONTRIBUTING                          | New layout, normalization tests, versioning                                            |
| **unified-internal-contracts** | README, ARCHITECTURE, CONFIGURATION, TESTING  | New repo docs                                                                          |
| **unified-trading-codex**      | 02-data/schema-governance.md                  | Schema evolution, versioning, extension pattern                                        |
| **unified-trading-codex**      | 05-infrastructure/cloud-agnostic-migration.md | Messaging (MessagingScope, Redis vs in-memory), EventSink vs cloud impl, storage tiers |
| **unified-trading-codex**      | 06-coding-standards/testing.md                | VCR SSOT, normalization testing, fixture ownership                                     |
| **unified-trading-codex**      | 06-coding-standards/error-handling.md         | Request-response-error, no empty try/except, error strategy, circuit breakers          |


### Cursor Rules Updates (Required)


| Rule                          | Location                                               | Content                                                                                    |
| ----------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| **Internal contracts import** | `.cursor/rules/` or `unified-trading-pm/cursor-rules/` | Import internal schemas from unified-internal-contracts; never from api-contracts.internal |
| **Schema extension**          | Same                                                   | Extend base schemas (BasePosition, etc.) from api-contracts; do not duplicate              |
| **VCR ownership**             | Same                                                   | VCR cassettes live in api-contracts; consumers reference path; no duplicates               |
| **No empty try/except**       | Same                                                   | No `except: pass` or `except Exception: pass`; every error path handled explicitly         |
| **Request-response-error**    | Same                                                   | Use api-contracts for external; unified-internal-contracts for internal; no ad-hoc         |


### PM Tracking (Required)


| Location                                                      | Purpose                                                             |
| ------------------------------------------------------------- | ------------------------------------------------------------------- |
| **unified-trading-pm/plans/ai/SCHEMA_OWNERSHIP_MIGRATION.md** | Master checklist: Phase 1/2/3 tasks, completion status, what we did |
| **unified-trading-pm/workspace-manifest.json**                | Add unified-internal-contracts, update api-contracts deps           |
| **unified-trading-pm/plans/ai/**                              | Link this plan; track schema evolution, cursor rules, doc updates   |


**Rule:** Every phase completion updates SCHEMA_OWNERSHIP_MIGRATION.md. No phase is "done" without doc + cursor rules + PM tracking updates.

---

## 9. Full Repo Inventory and Setup Pattern

### Repo Inventory (from workspace-manifest.json)

**Tier 0 libraries:** api-contracts, unified-config-interface, unified-events-interface, unified-cloud-interface, unified-reference-data-interface, execution-algo-library

**Tier 1 libraries:** unified-trading-services

**Tier 2 libraries:** unified-domain-client, unified-market-interface, unified-trade-execution-interface, unified-defi-execution-interface, unified-ml-interface, unified-feature-calculator-library, matching-engine-library, unified-position-interface (future)

**Services:** instruments-service, market-tick-data-handler, market-data-processing-service, features-calendar-service, features-delta-one-service, features-volatility-service, features-onchain-service, features-sports-service (future), ml-training-service, ml-inference-service, strategy-service, execution-services, alerting-system, pnl-attribution-service, position-balance-monitor-service, risk-and-exposure-service, strategy-validation-service

**Infrastructure:** unified-trading-deployment-v3, unified-trading-codex

**UIs:** backtest-ui, batch-audit-ui, trading-analytics-ui, live-health-monitor-ui, client-reporting-ui, logs-dashboard-ui, ml-deployment-ui, onboarding-ui, settlement-ui

### New Repo/Library Setup Pattern (Full Checklist)

When creating a **new library** (e.g. unified-internal-contracts, unified-sports-execution-interface):

1. **Scaffold**
  - Create repo directory
  - `pyproject.toml` (name, version, dependencies, [dev], ruff, pytest)
  - `src/<package>/` or flat `<package>/` structure
  - `tests/` with conftest.py
  - `README.md`, `docs/ARCHITECTURE.md`, `docs/CONFIGURATION.md`, `docs/TESTING.md`
  - `QUALITY_GATE_BYPASS_AUDIT.md` (empty or with exceptions)
  - `.cursorrules` (inherit workspace rules)
2. **CI/CD**
  - `scripts/quality-gates.sh` (ruff, basedpyright, pytest)
  - `scripts/quickmerge.sh` (or link to workspace)
  - `.github/workflows/quality-gates.yml`
  - `cloudbuild.yaml` (if published to Artifact Registry)
  - `Dockerfile` (if buildable)
3. **Dependencies**
  - Add to `pyproject.toml` with version ranges
  - Path deps for local dev: `api-contracts = { path = "../api-contracts" }`
  - Run `uv lock`
4. **Workspace manifest**
  - Add entry to `unified-trading-pm/workspace-manifest.json`
  - Set `arch_tier`, `doc_standard`, `dependencies`, `merge_level`
  - Add to `versions` if versioned
5. **Authentication / Artifact Registry**
  - If private lib: add to artifact registry config
  - Cloud Build auth for pulling base images
6. **Testing**
  - Unit tests for core logic
  - No circular imports (quality gate checks)
  - If uses external APIs: VCR via api-contracts or own cassettes (document owner)

When creating a **new service**:

- Same as library, plus: `config.py` (UnifiedCloudConfig), `Dockerfile`, `cloudbuild.yaml`, `tests/unit/test_event_logging.py`, `.env.example`

When creating a **new UI**:

- `package.json`, `tsconfig.json`, `vite.config` or equivalent, `docs/TESTING.md`, ESLint, tsc

---

## 10. Repos Requiring Changes (This Plan)


| Repo                                   | Change                                                                                             | Tier |
| -------------------------------------- | -------------------------------------------------------------------------------------------------- | ---- |
| **api-contracts**                      | Restructure: api_contracts_external/, unified_normalised_contracts/                                | 0    |
| **unified-internal-contracts**         | NEW — messaging.py (topic names, GCP/Redis/AWS); extract pubsub, ml, risk, etc.                    | 0    |
| **unified-trading-services**           | Redis vs in-memory, QueueEventSink AWS, StateStore, EventSink/EventReader, StorageEventSink rename | 1    |
| **unified-trade-execution-interface**  | BaseExecutionAdapter, BaseCLOBAdapter; rename BaseOrderAdapter                                     | 2    |
| **unified-defi-execution-interface**   | BaseAMMAdapter (swaps, pools)                                                                      | 2    |
| **unified-sports-execution-interface** | NEW — BaseSportsAdapter (Betfair reuses CLOB; Pinnacle uses Sports)                                | 2    |
| **unified-trading-pm**                 | Add new repos to workspace-manifest.json                                                           | —    |
| **unified-trading-codex**              | Document messaging, storage tiers, VCR SSOT, testing ownership                                     | —    |


---

## 11. Implementation Todos (Actionable)

### Messaging and Storage (UCS)

- **msg-redis-inmem**: Document Redis (multi-thread) vs in-memory (single-thread) in codex and UCS config
- **msg-redis-reuse**: Reuse UTD v3 RedisCache/aioredis patterns; add Redis backend to UCS messaging (don't rebuild)
- **msg-cross-vm-redis**: Add cross-VM Redis (Memorystore/ElastiCache) as option — faster than Pub/Sub when configured
- **msg-aws**: Implement `get_event_publisher()` with GCP Pub/Sub, AWS SNS+SQS, Redis backends
- **storage-rename**: Rename GCSEventSink → StorageEventSink (or GcsEventSink as implementation), PubSubEventSink → QueueEventSink (backward-compat alias)
- **storage-statestore**: Define StateStore interface (get/set/compare-and-set, scan_by_key_prefix); implement Redis, DynamoDB, CloudSQL/Aurora, SQLite backends; define rebuild-from-log flow
- **storage-eventsink**: Implement GcsEventSink, S3EventSink, LocalFsEventSink; add EventReader interface for replay

### Schema Repos

- **api-contracts-restructure**: Create api_contracts_external/, unified_normalised_contracts/ subpackages; migrate existing
- **unified-internal-repo**: Create unified-internal-contracts repo with full setup (pyproject, quality gates, quickmerge, manifest, docs)
- **dep-enforcement**: Quality gate check — api-contracts must not import unified-internal-contracts
- **dep-enforcement-cloud-sdks**: Quality gate check — unified-internal-contracts must not import cloud SDKs (google-cloud-*, boto3, redis clients)

### Execution Adapters

- **utei-base**: Add BaseExecutionAdapter (thin: lifecycle, ids, capability flags); rename BaseOrderAdapter → BaseCLOBAdapter
- **udei-amm**: Add BaseAMMAdapter in UDEI (DeFi swaps, pools: Uniswap, Curve)
- **sports-adapter**: Create BaseSportsAdapter (Betfair reuses CLOB; Pinnacle uses Sports); new repo or UTEI extension

### Manifest and Integration

- **manifest-update**: Add unified-internal-contracts, unified-sports-execution-interface to workspace-manifest.json with deps, tier, merge_level
- **consumer-update**: Update all services/libraries that import from api_contracts.internal to use unified-internal-contracts
- **UIC adoption**: Add `unified-internal-contracts` dep + use `LifecycleEventType` in log_event. Done: execution-services, unified-trading-services, market-data-processing-service, instruments-service, market-tick-data-handler, risk-and-exposure-service, features-calendar-service, features-delta-one-service, features-volatility-service, features-onchain-service, ml-training-service, ml-inference-service, strategy-service, position-balance-monitor-service, pnl-attribution-service, alerting-system. Remaining (if in workspace): features-sports-service, strategy-validation-service.

### Testing and VCR

- **vcr-ownership**: Document in codex: api-contracts owns VCR (HTTP only; WebSocket capture is separate); consumers reference path; no duplicates
- **testing-ssot**: Add codex section: who owns unit/integration/VCR per repo type

### Codex Documentation

- **codex-messaging**: Update cloud-agnostic-migration.md with Redis vs in-memory vs Pub/Sub
- **codex-storage**: Document hot state vs append-only log; StateStore; rebuild-from-log; OLAP vs object tiers
- **codex-testing**: Add 06-coding-standards/testing.md section on VCR SSOT, fixture ownership
- **codex-errors**: Add 06-coding-standards/error-handling.md — request-response-error symmetry, no empty try/except, error strategy (retry/fail-fast/exit-job), circuit breakers

### PM Tracking and Cursor Rules (Required Every Phase)

- **pm-migration-doc**: Create `unified-trading-pm/plans/ai/SCHEMA_OWNERSHIP_MIGRATION.md` at start; update after each phase
- **cursor-rules**: Add/update rules in `unified-trading-pm/cursor-rules/` (or `.cursor/rules/`); sync via quickmerge
- **plan-link**: Link this plan from SCHEMA_OWNERSHIP_MIGRATION.md for traceability

---

## 12. Per-Repo Update Checklist (All Repos)

Every repo must be audited and updated. Non-compliant code removed or adjusted.


| Repo                                   | Updates                                                                           |
| -------------------------------------- | --------------------------------------------------------------------------------- |
| **api-contracts**                      | Restructure; add request/response/errors; normalisation tests                     |
| **unified-internal-contracts**         | NEW — create repo, request/response/errors                                        |
| **unified-trading-services**           | Event/storage; circuit breaker; error handling utilities                          |
| **unified-config-interface**           | Config error schemas (if not already)                                             |
| **unified-events-interface**           | Event error schemas                                                               |
| **unified-cloud-interface**            | Storage error schemas                                                             |
| **unified-domain-client**              | Use normalised schemas; remove ad-hoc errors                                      |
| **unified-market-interface**           | Use normalised request/response/errors; translation only                          |
| **unified-trade-execution-interface**  | Use normalised request/response/errors; BaseExecutionAdapter, BaseCLOBAdapter     |
| **unified-defi-execution-interface**   | BaseAMMAdapter; same normalised pattern                                           |
| **unified-ml-interface**               | Use internal contracts                                                            |
| **unified-feature-calculator-library** | Use internal contracts                                                            |
| **unified-position-interface**         | Use normalised; extend BasePosition                                               |
| **All 14 services**                    | Switch to unified-internal-contracts; remove empty try/except; add error strategy |
| **All 9 UIs**                          | Use config/event error handling; no ad-hoc                                        |
| **unified-trading-codex**              | Document all patterns                                                             |
| **unified-trading-pm**                 | Manifest; SCHEMA_OWNERSHIP_MIGRATION.md                                           |


---

## 13. Implementation Verification (Deep Check)

*Last verified via parallel explore subagents; token-optimized checks.*

### Implemented


| Area                                | Status  | Evidence                                                                                                                                                             |
| ----------------------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **api-contracts restructure**       | Partial | `api_contracts_external/`, `unified_normalised_contracts/` exist; `tests/test_normalization.py` exists                                                               |
| **unified-internal-contracts repo** | Done    | Repo exists; in workspace-manifest.json; `messaging.py` has MessagingScope (IN_PROCESS, SAME_VM, CROSS_VM); events.py has LifecycleEventEnvelope, LifecycleEventType |
| **Manifest**                        | Done    | unified-internal-contracts, unified-sports-execution-interface (future) in workspace-manifest.json                                                                   |
| **UTEI adapters**                   | Done    | BaseExecutionAdapter, BaseCLOBAdapter in base_adapter.py; BaseOrderAdapter = legacy alias; BaseSportsAdapter in UTEI                                                 |
| **UDEI**                            | Done    | BaseAMMAdapter in amm_adapter.py                                                                                                                                     |
| **UCS StateStore**                  | Done    | StateStore Protocol in core/state_store.py (get, set, compare_and_set, scan_by_key_prefix, rebuild_from_log)                                                         |
| **Quality gate: api-contracts**     | Done    | quality-gates.sh fails on imports of unified_trading_services, unified_domain_client, unified_internal_contracts                                                     |
| **Quality gate: internal no cloud** | Partial | unified-internal-contracts quality-gates.sh checks google.cloud, boto3; redis only in pyproject grep, not code scan                                                  |
| **Codex MessagingScope**            | Done    | 04-architecture/messaging-scope.md documents IN_PROCESS, SAME_VM, CROSS_VM                                                                                           |
| **VCR ownership**                   | Partial | 02-data/vcr-cassette-ownership.md has SSOT; not in 06-coding-standards/testing.md per plan                                                                           |


### Gaps (not fully implemented)


| Gap                                               | Plan requirement                                 | Current state                                                               |
| ------------------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------- |
| **InternalPubSubTopic**                           | Move to unified-internal-contracts               | Still in api-contracts/internal/pubsub.py                                   |
| **EventSinkSpec**                                 | In unified-internal-contracts events (contracts) | **DONE** — added to events.py, exported                                     |
| **EventReader**                                   | Interface in UEI or UCI                          | **DONE** — Protocol in UCS event_sink.py                                    |
| **GCSEventSink rename**                           | StorageEventSink or GcsEventSink                 | **DONE** — GcsEventSink + GCSEventSink alias in UCS                         |
| **S3EventSink, LocalFsEventSink**                 | Implementations in UCS                           | **DONE** — both in UCS event_sink.py                                        |
| **QueueEventSink AWS**                            | SNS+SQS in UCS                                   | **DONE** — QueueEventSink in UCS, uses UCI get_queue_client(provider="aws") |
| **06-coding-standards/error-handling.md**         | Request-response-error, no empty try/except      | **DONE** — created in codex                                                 |
| **06-coding-standards/testing.md**                | VCR SSOT, fixture ownership                      | **DONE** — section added, links to 02-data/vcr-cassette-ownership.md        |
| **05-infrastructure/cloud-agnostic-migration.md** | MessagingScope, EventSink vs cloud impl          | **DONE** — subsection added, link to 04-architecture/messaging-scope.md     |
| **SCHEMA_OWNERSHIP_MIGRATION.md**                 | PM tracking in plans/ai                          | **DONE** — created with Phase 1/2/3 checklist                               |
| **unified-internal-contracts: redis in code**     | CI fail if redis client imported in code         | **DONE** — quality-gates.sh rg for import redis / from redis in source      |


### Todo status vs reality

- Plan marks msg-redis-inmem, storage-fast, utei-clob, sports-adapter, amm-adapter, manifest-update, dep-enforcement, dep-enforcement-cloud-sdks as completed — **matches** (dep-enforcement-cloud-sdks now full: redis code scan added).
- msg-aws: **completed** — QueueEventSink added to UCS.
- api-contracts-restructure, unified-internal-repo, vcr-ownership: partially/done (dirs, repo, codex VCR section).

### Post-completion note (InternalPubSubTopic)

Canonical topic names live in **unified-internal-contracts** as `MessagingTopic`. **api-contracts** keeps `InternalPubSubTopic` for backward compatibility (no unified-* import). New code should use `unified_internal_contracts.messaging.MessagingTopic`.
