---
doc_type: codex-ssot
title: "`odum-paper` Client Zero — Representative Paper Account"
summary:
  The odum-paper/odum-live representative-account model — every strategy instance is auto-subscribed by internal client
  odum-paper (fills at requested price = pure strategy alpha), giving every instance a continuous backtest→paper→live
  P&L series. Non-special-casing rule (no `client_id == "odum-paper"` branch anywhere), $100-$1000 seed, unbounded
  retention.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [client-reporting-api, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [strategy, reconciliation, data-correctness, ml, monitoring, uac]
related:
  [
    ../../09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    ../../09-strategy/architecture-v2/performance-overlay.md,
    ../../04-architecture/shard-level-failure-isolation.md,
    /codex/14-customer-journeys/shared-core/strategy-version-governance.md,
  ]
created: 2026-04-21
authoritative_for: [odum-paper/odum-live representative paper-account model]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/performance-overlay.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
    /codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    /codex/14-customer-journeys/shared-core/strategy-version-governance.md,
  ]
owner:
last_reviewed:
code_refs:
---

# `odum-paper` Client Zero — Representative Paper Account

> **Status:** canonical (2026-04-21) **Owner:** Strategy Architecture v2 + Platform Ops **SSOT for:**
> `unified-api-contracts/unified_api_contracts/internal/domain/client/registry.py` seed rows (`odum-paper`,
> `odum-live`). **Plan:**
> [`plans/archive/strategy_lifecycle_maturity_model_2026_04_21.plan.md`](../../../plans/archive/strategy_lifecycle_maturity_model_2026_04_21.plan.md)
> **Cross-refs:**
> [`../../09-strategy/architecture-v2/strategy-lifecycle-maturity.md`](../../09-strategy/architecture-v2/strategy-lifecycle-maturity.md)
> ·
> [`../../09-strategy/architecture-v2/strategy-catalogue-3tier.md`](../../09-strategy/architecture-v2/strategy-catalogue-3tier.md)
> ·
> [`../../09-strategy/architecture-v2/performance-overlay.md`](../../09-strategy/architecture-v2/performance-overlay.md)
> · `CLAUDE.md` "Batch = Live" section.

---

## §1 — The rationale

A strategy instance cannot earn trust without a **continuous, attributable P&L record** covering backtest → paper →
live. But who runs the paper trade in production, every day, for every instance, at scale?

**Answer:** Odum runs it. Every strategy instance is automatically subscribed by a single internal client called
`odum-paper`. That client's `account_type = paper` routes fills through the execution-service matching engine (zero
execution alpha — fills at requested price) and records the resulting P&L alongside every other client's P&L.

This is the representative-paper-account model. Its three jobs:

1. **Forces "paper before live" discipline.** An instance cannot graduate to `live_early` without ≥30d of `odum-paper`
   fills at `paper_stable`.
2. **Gives every FOMO tearsheet a backtest+paper+live story** — sourced from one client's series, not patched together
   from multiple real clients.
3. **Isolates execution alpha** — because `odum-paper` fills at requested price, its P&L equals **strategy alpha only**.
   The gap between `odum-paper` P&L and `odum-live` (or any real client's) P&L **is** the execution alpha. This is the
   instrument the execution-service team optimises against.

---

## §2 — The critical non-special-casing rule

`odum-paper` is a **regular Client row**, not a special case in code.

```python
# unified_api_contracts/internal/domain/client/registry.py
Client(
    client_id="odum-paper",
    org="odum-research",
    account_type="paper",
    seed=True,
)
Client(
    client_id="odum-live",
    org="odum-research",
    account_type="live",
    seed=True,
)
```

Downstream services (position-balance-monitor-service, execution-service, strategy-service, client-reporting-api) do
**not** check `client_id == "odum-paper"` anywhere. They all do the normal thing for a client with
`account_type = paper`: the matching engine fills, positions tracked in `positions/{client_id}/`, P&L recorded per
instance.

**Why this matters.** The moment `odum-paper` becomes a special case, the entire representative-paper-account premise
collapses — "the paper run is the same code path every real paper client sees". Batch=live applies. If someone adds
`if client_id == "odum-paper"` anywhere in the fleet, it is a bug.

Real clients added later:

- `account_type = paper` — onboarding a new client in UAT; shares `odum-paper`'s code path.
- `account_type = live` — live client; routes to real venue adapters.

The `odum-live` twin exists for the same reason — so instances that graduate to `live_early` have a **real live fills
series** that is still owned by Odum, not a real client. Real-client P&L is separate and per-client.

---

## §3 — Lifecycle

### When an instance is created

Plan A Phase 1 `p1-strategy-instance-5dim-rewrite` expands the registry to ~200-300 instances. Each new instance
triggers:

1. `strategy-service` reads the catalogue from UAC at startup.
2. For every instance with `maturity_phase ≥ smoke` AND `odum-paper` not yet subscribed, it creates a subscription row
   via the normal client subscription flow.
3. `execution-service` receives the subscription → spins up a matching-engine session per instance.
4. Backtest re-runs (if applicable) populate the `odum-paper` backtest series.

### Daily cadence

- Paper fills stream to `positions/odum-paper/`.
- `position-balance-monitor-service` rolls up P&L into `pnl_timeseries/(odum-paper, instance_id)`.
- `client-reporting-api` exposes the series at `GET /api/v1/strategy-instances/{id}/performance?views=paper` (Plan C
  Phase 1).
- `LifecycleReloader` (UTL, 5-min poll) re-reads current maturity phase; if Firestore flipped the instance to `retired`,
  the matching-engine session unsubscribes on next tick.

### When an instance graduates to live

- Admin editor moves the instance to `live_early`.
- `odum-live` subscribes (not `odum-paper` — they run **in parallel**; `odum-paper` keeps running so paper/live drift is
  measurable).
- Real live fills stream to `positions/odum-live/` through the venue adapter.
- Both series feed the Performance Overlay (Plan C) — three coloured lines: backtest (blue), paper (amber), live
  (emerald).

### When an instance retires

- Admin editor flips to `retired`.
- Both `odum-paper` and `odum-live` unsubscribe on next reloader tick.
- Historical P&L series **preserved** — never truncated. Retired instances still appear in Reports historical
  attribution and Performance Overlay for their run window.

---

## §4 — Capital seeding

Each instance starts paper trading with a **configurable per-instance seed** in a small range.

| Setting                    | Value / pattern                                     |
| -------------------------- | --------------------------------------------------- |
| Default seed               | $1,000 notional                                     |
| Configurable range         | $100 – $1,000 per instance                          |
| Seed unit                  | Expressed in the instance's `share_class` currency  |
| Where set                  | Admin editor → instance config row (Plan B Phase 2) |
| Share-class interpretation | BTC share class = 0.01 BTC (≈$1,000 at $100k BTC)   |

**Why this range.** Too small ($10) and rounding to exchange tick sizes distorts the PnL signal. Too large ($10,000+ per
instance × 200-300 instances = $2M-3M paper exposure) and the Batch=Live assumption that matching-engine fills simulate
fairly starts to fray (market-impact effects the matching engine does not model).

**Not configurable at scale.** The seed is a starting point — the matching engine compounds paper P&L into the running
paper equity. A winning strategy's paper equity drifts up over time; the seed is just the initial condition.

---

## §5 — Retention (unbounded)

Paper P&L series are retained **forever**. Storage cost is trivial (daily close snapshots + per-fill records per
instance ≈ tens of MB/year per instance × 300 instances = 10s of GB/year total in BigQuery). The value — having 3+ years
of continuous paper on every instance when a FOMO tearsheet is being built for a new client — is the entire commercial
premise.

Retention is enforced at the `pnl_timeseries/` collection level — no TTL, no retention policy, no cleanup job. Retired
instances' series remain queryable indefinitely.

---

## §6 — Reality-vs-expected monitoring

`odum-paper` is also a real-time monitor for every live instance. The "expected" curve is the paper run of the same
instance; "reality" is the live run (`odum-live` OR any real client on that instance).

### Drift detection

- `client-reporting-api` computes rolling **paper-vs-live residual** per instance per day.
- If the residual exceeds a per-archetype threshold (default: 5% daily / 15% 7d), emit `STRATEGY_PAPER_LIVE_DRIFT` →
  routed to Observe · Risk dashboard.
- Operator drills into per-venue breakdown (Performance Overlay `per_venue=true` mode) to identify which venue(s) are
  causing execution degradation.

### Alpha decay on scale

Because `odum-paper` runs at the **fixed seed**
($1,000) and real clients run at their allocation size, divergence
between the two series measures **alpha decay on capital scaling**. A strategy that matches paper at $1K
but underperforms at $1M has market-impact / capacity issues.

This is the allocator signal surfaced in Reports → Allocator View → 3-way overlay (Plan C Phase 3).

### What is **not** a drift

- Fee drag (matching engine assumes taker fees per venue profile — real fees can differ slightly).
- Funding-rate variance on perps (matching engine uses settled funding at snapshot; live is real-time).
- Timing noise (matching engine fills at requested price; live fills at slippage).

The drift alert fires only when residual exceeds the threshold **sustained** over the rolling window — short-term noise
self-cancels.

---

## §7 — Operational guarantees

- **Subscription idempotency** — re-running the seeder never double-subscribes `odum-paper` to an instance.
- **Failure isolation** — if the matching engine for one instance fails, the shard-level isolation rule
  ([`shard-level-failure-isolation.md`](../../04-architecture/shard-level-failure-isolation.md)) keeps the rest running.
- **Circuit breakers** — `odum-paper` has the same circuit breaker wiring as any other paper client. A runaway instance
  (e.g. buggy config emitting 10K orders/min) hits the circuit and gets paused; `STRATEGY_CIRCUIT_BREAKER` event fires.
- **Daily reconciliation** — position-balance-monitor-service reconciles `odum-paper` positions at UTC close, exactly as
  it does for real clients.
- **Events** — `STARTED/STOPPED/FAILED` lifecycle events emitted per `odum-paper` subscription, same as any client.

---

## §8 — FAQ

**Q: Why not just run backtests and call that "paper"?**

Backtests don't exercise the service mesh — no position-balance-monitor, no execution-service matching engine, no
risk-and-exposure-service. Paper runs the full pipeline with the `odum-paper` client, so the gap between backtest and
live attributes properly (code-path gap vs execution-alpha gap). CLAUDE.md "Batch = Live" is authoritative.

**Q: Why have `odum-live` too?**

Because instances that graduate to `live_early` need a live P&L series **owned by Odum**, not by a real client. Real
clients' live series are private and cannot be used to drive FOMO tearsheets. `odum-live`'s series **is** the
representative live run that appears on tearsheets.

**Q: Does `odum-live` cost real money to run?**

Yes — it's live trading. But at seed scale ($100-$1,000 per instance), the cost of capital is small relative to the
commercial value of having honest live-vs-paper overlays on every instance. Risk is bounded by the seed and the circuit
breakers.

**Q: What about client leak? Does a FOMO tearsheet show a real client's performance?**

No. The live series on a FOMO tearsheet is **always** `odum-live`'s run of that instance, not any real client's. See
[`memory/project_fomo_tearsheets_show_live_is_odum_own_run_2026_04_21.md`] for the full discussion.

**Q: What if a real client subscribes at a larger size than `odum-paper`'s seed?**

That's expected and is exactly the alpha-decay-on-scale signal in §6. The three-way overlay reveals the divergence.

---

## §9 — Cross-references

- [`../../09-strategy/architecture-v2/strategy-lifecycle-maturity.md`](../../09-strategy/architecture-v2/strategy-lifecycle-maturity.md)
  — §5 where the seed rows are defined.
- [`../../09-strategy/architecture-v2/performance-overlay.md`](../../09-strategy/architecture-v2/performance-overlay.md)
  — the chart primitive driven by these series.
- [`../../09-strategy/architecture-v2/strategy-catalogue-3tier.md`](../../09-strategy/architecture-v2/strategy-catalogue-3tier.md)
  — Tier 3 FOMO tearsheets consume these series.
- [`../../04-architecture/shard-level-failure-isolation.md`](../../04-architecture/shard-level-failure-isolation.md) —
  per-instance failure isolation applies to `odum-paper` subscriptions.
- `CLAUDE.md` → "Batch = Live" section — the code-path-identity premise this model depends on.
