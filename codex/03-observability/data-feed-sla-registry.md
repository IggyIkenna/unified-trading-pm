---
doc_type: codex-ssot
title: Data-Feed SLA Registry
summary: "Feed-SLA registry (SSOT in data_freshness.py — DataFreshnessContract + ALL_FRESHNESS_CONTRACTS): per-feed
  max_age/warn_age/cadence/criticality (critical/important/informational) plus refetch_action Layer-0 self-healing; four
  sub-dicts (MARKET_TICK/FEATURE/ML/ACCOUNT_STATE_FRESHNESS), CI-enforced no-orphan + warn<max invariants;
  cross-validated with ALERT_THRESHOLDS tick_staleness (300s floor)."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    alerting-service,
    deployment-service,
    execution-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [data-feed-sla, data-quality, self-healing, monitoring, reconciliation, observability]
related:
  [
    /codex/03-observability/alerting.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/reconciliation-age-tracking.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-06-20
authoritative_for: [data-feed SLA registry, feed freshness contracts + refetch_action binding]
referenced_by:
  [
    /codex/03-observability/alerting.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/dependency-health-policy.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
owner:
last_reviewed: 2026-06-20
code_refs:
---

# Data-Feed SLA Registry

> **SSOT**: `unified_api_contracts/internal/reference/data_freshness.py` — `DataFreshnessContract` +
> `ALL_FRESHNESS_CONTRACTS`. This doc describes the registry as the canonical feed-SLA contract; do NOT re-declare
> freshness thresholds anywhere else in the codebase.

Shipped 2026-06-19/20 per `plans/archive/2026_08/data_feed_sla_registry_and_active_self_healing_2026_06_19.md`.

---

## Purpose

Every data feed the system relies on has a named SLA: how fresh it must be, how serious a staleness breach is, and which
recovery action to fire. Before this registry existed, freshness thresholds were scattered across four locations
(`MARKET_TICK_FRESHNESS`, `ALERT_THRESHOLDS["tick_staleness_seconds"]`, per-service literals) and coupled by comments,
not code. The registry is the single home; every consumer reads it — nothing re-declares a threshold inline.

---

## `DataFreshnessContract` — schema

Defined in `unified_api_contracts.internal.reference.data_freshness`:

| Field                      | Type                                                | Meaning                                                                                                                                                                                                                      |
| -------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `source`                   | `str`                                               | Feed identifier (venue name / data domain). Also serves as the dict key in each sub-dict.                                                                                                                                    |
| `asset_group`              | `Literal[...]`                                      | Market domain: `"cefi"` / `"defi"` / `"tradfi"` / `"sports"` / `"prediction"` / `"execution"` (account-state feeds).                                                                                                         |
| `max_age_seconds`          | `int`                                               | Hard ceiling — a feed older than this value is **stale**; consumers must act.                                                                                                                                                |
| `warn_age_seconds`         | `int`                                               | Soft warning threshold (`warn_age_seconds < max_age_seconds` always; CI gate asserts this).                                                                                                                                  |
| `expected_cadence_seconds` | `int`                                               | Expected feed update cadence — used by liveness monitors to detect a silent producer.                                                                                                                                        |
| `criticality`              | `Literal["critical", "important", "informational"]` | Determines what consumers do on breach (see tiers below).                                                                                                                                                                    |
| `refetch_action`           | `str \| None`                                       | Layer-0 recovery action to fire on staleness breach. `None` for `informational` feeds. Format: `"refetch-feed:<source>"` (REST re-pull) or `"rotate-websocket:<source>"` (ws-session rotation — the ws-sourced live venues). |

**Invariant (CI-enforced):** `warn_age_seconds < max_age_seconds` for every contract in `ALL_FRESHNESS_CONTRACTS`.

---

## Criticality tiers — what each level does

| Tier                | Order-flow impact                                                                         | Alert routing                                                                                                 | Recovery action                                                                |
| ------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **`critical`**      | Blocks order flow immediately — `freshness_gate.py` raises `DataStalenessError` on breach | WARN→CRITICAL/HIGH escalation via per-feed `CircuitBreaker`; sustained breach adds advisory `reduce_position` | `refetch_action` fires (SILENT_RETRY first, then escalate on repeated failure) |
| **`important`**     | Does NOT block orders; emits `DATA_STALE` warning and degrades signal quality             | WARN→HIGH escalation on repeated failure                                                                      | `refetch_action` fires (same recovery path, lower severity ceiling)            |
| **`informational`** | Log only — no order-flow impact, no alert escalation                                      | Telegram INFO                                                                                                 | `refetch_action = None` — no active recovery                                   |

---

## Sub-dicts and `ALL_FRESHNESS_CONTRACTS`

The registry organises contracts into four purpose-aligned sub-dicts, all merged into `ALL_FRESHNESS_CONTRACTS`:

| Sub-dict                  | Covers                                                                | Typical criticality           |
| ------------------------- | --------------------------------------------------------------------- | ----------------------------- |
| `MARKET_TICK_FRESHNESS`   | Real-time market-data feeds (~22 venues across CeFi, DeFi, TradFi)    | `critical` for live venues    |
| `FEATURE_FRESHNESS`       | Computed feature pipelines (delta-one, volatility, onchain)           | `important` / `informational` |
| `ML_FRESHNESS`            | ML model outputs and prediction feeds                                 | `important`                   |
| `ACCOUNT_STATE_FRESHNESS` | Execution-layer account / position / reconciliation state (see below) | `critical`                    |

`ALL_FRESHNESS_CONTRACTS: dict[str, DataFreshnessContract]` is the flat O(1) lookup every consumer uses. Its integrity
is enforced by a CI test (`tests/internal/unit/test_freshness_ssot_agreement.py` — the no-orphan-feed gate):

- `ALL_FRESHNESS_CONTRACTS` == exact union of all four sub-dicts (no orphan, no missing entry).
- Every contract's `.source` matches its dict key.
- `warn_age_seconds < max_age_seconds` for every contract.
- `criticality` is one of the three valid literals.

---

## Account-state feeds (`ACCOUNT_STATE_FRESHNESS`)

Added 2026-06-19 to close the gap identified by the Blue Flame comparison. These feeds cover execution-layer state, not
market data, so their `asset_group` is `"execution"`:

| Feed key             | `max_age_seconds` | `warn_age_seconds` | Criticality | Notes                                                                                                                                                      |
| -------------------- | ----------------- | ------------------ | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `account_snapshot`   | 120               | 60                 | `critical`  | Live account balance / equity snapshot from venues.                                                                                                        |
| `positions_snapshot` | 120               | 60                 | `critical`  | Live position state from venues.                                                                                                                           |
| `reconciliation_age` | 2400              | 1200               | `critical`  | Age of the most-recent successful reconciliation run. `warn` = SEV1 band; `max` = SEV0 band (per `/codex/04-architecture/reconciliation-age-tracking.md`). |

These feeds are reachable via `ALL_FRESHNESS_CONTRACTS` and via
`from unified_api_contracts.internal import ACCOUNT_STATE_FRESHNESS`.

---

## `refetch_action` field and active self-healing

Every `critical` and `important` contract carries a bound Layer-0 action id — `refetch-feed:<source>` (REST re-pull)
or, for the ws-sourced live venues (binance/bybit/okx/coinbase/hyperliquid/deribit), `rotate-websocket:<source>`
(ws-session rotation — a REST re-pull cannot revive a dead socket). The id names the Layer-0 recovery action that
fires when the feed is stale:

- **Layer-0 script (refetch)**: `deployment-service/scripts/recovery/refetch_feed.py` — looks up the contract, invokes
  the owning-service CLI
  (`market-tick-data-service --operation download --mode batch --asset-group <ag> --venues <source> --day <today-UTC>`),
  emits `AgentActionEvent`, and enforces a per-feed cooldown storm-guard.
- **Layer-0 script (rotate)**: `deployment-service/scripts/recovery/rotate_websocket.py` (`ActionType.ROTATE_WEBSOCKET`)
  — same storm guards; drops the UTL `ws_rotation_request` sentinel, which the owning `WsSessionManager` consumes on
  its next watchdog tick to rotate the session per the venue's `WsProtocolSpec`. SSOT:
  `/codex/04-architecture/venue-websocket-resilience.md`.
- **UAC enum**: `ActionType.REFETCH_FEED` / `ActionType.ROTATE_WEBSOCKET` in `unified_api_contracts`.
- **UTL registry**: `RecoveryScriptRegistry` entries map both action types to their scripts.
- **Escalation**: `alerting-service/rules/feed_refetch_rules.py` — stale critical feed → fire the feed's BOUND action
  (resolved from the contract — refetch or rotate) as SILENT_RETRY → per-feed `CircuitBreaker` (3 fails/30 min)
  escalates WARN→CRITICAL/HIGH via
  `route_event_with_explicit_channels` → sustained breach adds advisory `reduce_position`.

**Limitation (known, tracked):** the re-fetch uses a coarse `--day` window. Finer `--shard-key` targeting is a future
tightening (security_and_cross_cutting_master B.2 Phase 5). Feeds in the `execution`, `feature`, and `ml` domains raise
`UnroutableFeedError` because their owning CLIs are outside MTDS scope — the escalation ladder handles them directly.

Full architecture: `/codex/04-architecture/autonomous-recovery-matrix.md` § "Stale feed — refetch-feed Layer-0 action".

---

## One freshness home — cross-validation with `ALERT_THRESHOLDS`

`ALERT_THRESHOLDS["tick_staleness_seconds"]` in `unified_api_contracts/canonical/crosscutting/alerting/thresholds.py`
historically carried the same number as `MARKET_TICK_FRESHNESS` thresholds, coupled only by a comment. The freshness
numbers now have **exactly one authoritative home** in `data_freshness.py`; the alert threshold is cross-validated (not
derived at import time, to avoid a circular import) by:

```
unified-api-contracts/tests/internal/unit/test_freshness_ssot_agreement.py
```

This test asserts that `ALERT_THRESHOLDS["tick_staleness_seconds"]` (the coarse alerting floor, 300 s by default) is ≥
the strictest real-time per-venue `max_age_seconds` in `MARKET_TICK_FRESHNESS`, and pins a regression guard at 300 s.
Any change to the alert threshold that would make it stricter than the per-venue contract fails CI immediately.

---

## Consumers

All consumers read `ALL_FRESHNESS_CONTRACTS` (or a sub-dict) from the registry — no inline literals:

| Consumer                                                  | What it does                                                                                                              |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `execution-service/validation/freshness_gate.py`          | `assert_market_data_fresh` — raises `DataStalenessError` for `critical` breaches; blocks orders.                          |
| `strategy-service/validation/freshness_gate.py`           | `assert_feature_fresh` — raises for `critical`, emits `DATA_STALE` warning for `important`.                               |
| `mdps/monitors/feature_freshness.py`                      | Feature-feed freshness monitor — checks `FEATURE_FRESHNESS` contracts on each pipeline tick.                              |
| `unified_trading_library/monitors/freshness_monitor.py`   | Generic wrapper around `DataFreshnessContract`; used by any service that needs a per-feed liveness probe.                 |
| `deployment-service/scripts/recovery/refetch_feed.py`     | Layer-0 recovery — reads `refetch_action` to drive active re-fetch on stale critical/important feeds.                     |
| `deployment-service/scripts/recovery/rotate_websocket.py` | Layer-0 recovery — ws-session rotation for `rotate-websocket:`-bound feeds (drops the WsSessionManager request sentinel). |
| `alerting-service/rules/feed_refetch_rules.py`            | Escalation ladder for repeated refetch failures.                                                                          |

---

## Related

- `/codex/04-architecture/autonomous-recovery-matrix.md` — Layer-0 `refetch-feed` action + decision tree
- `/codex/03-observability/alerting.md` — alert routing; `tick_staleness_seconds` cross-validation note
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator staleness as a feed in this registry
- `/codex/04-architecture/reconciliation-age-tracking.md` — recon-age SEV1/SEV0 bands (the `reconciliation_age` contract
  SLA source)
